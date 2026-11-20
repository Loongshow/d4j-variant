# Run R38: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.collections.FastArrayList::effectiveKey`
- Gold file in the workspace: `src/java/org/apache/commons/collections/FastArrayList.java` (lines 431–436)
- Method the failing test calls (facade): `org.apache.commons.collections.ExtendedProperties::getInclude`
- Failing test: `org.apache.commons.collections.TestExtendedProperties::testInclude`
- Text removed from the gold (the omission): `return defaultKey;         }         return key.length() > 0 ? key : null;`
- The same place in the variant now reads: `return defaultKey;         }         return key;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  431        public static String effectiveKey(String key, String defaultKey) {
  432            if (key == null) {
  433 >>             return defaultKey;
  434            }
  435 >>         return key;
  436        }
```
