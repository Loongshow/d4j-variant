# Run R02: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.collections.CursorableLinkedList::appendOnce`
- Gold file in the workspace: `src/java/org/apache/commons/collections/CursorableLinkedList.java` (lines 620–630)
- Method the failing test calls (facade): `org.apache.commons.collections.list.SetUniqueList::decorate`
- Failing test: `org.apache.commons.collections.list.TestSetUniqueList::testFactory`
- Text removed from the gold (the omission): `if (positions.containsKey(elements[i]) == false) {                 positions.put(elements[i], new Integer(i));             }`
- The same place in the variant now reads: `positions.put(elements[i], new Integer(i));`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  620        public static void appendOnce(List list, Object[] elements) {
  621            final Map positions = new HashMap();
  622            for (int i = 0; i < elements.length; i++) {
  623 >>             positions.put(elements[i], new Integer(i));
  624            }
  625            for (int i = 0; i < elements.length; i++) {
  626                if (((Integer) positions.get(elements[i])).intValue() == i) {
  627                    list.add(elements[i]);
  628                }
  629            }
  630        }
```
