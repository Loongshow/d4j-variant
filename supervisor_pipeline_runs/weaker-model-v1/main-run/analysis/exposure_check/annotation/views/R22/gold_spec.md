# Run R22: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang.ArrayUtils::appendEscapedChars`
- Gold file in the workspace: `src/java/org/apache/commons/lang/ArrayUtils.java` (lines 2778–2788)
- Method the failing test calls (facade): `org.apache.commons.lang.StringEscapeUtils::escapeHtml`
- Failing test: `org.apache.commons.lang.StringEscapeUtilsTest::testEscapeHtml`
- Text removed from the gold (the omission): `String entityName = Entities.HTML40.entityName(c);             if (entityName == null && c > 0x7F) {                 entityName = "#" + Integer.toString(c, 10);             }`
- The same place in the variant now reads: `String entityName = Entities.HTML40.entityName(c);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 2778        public static void appendEscapedChars(StringBuffer buffer, char[] array) {
 2779            for (int i = 0; i < array.length; i++) {
 2780                char c = array[i];
 2781 >>             String entityName = Entities.HTML40.entityName(c);
 2782                if (entityName == null) {
 2783                    buffer.append(c);
 2784                } else {
 2785                    buffer.append('&').append(entityName).append(';');
 2786                }
 2787            }
 2788        }
```
