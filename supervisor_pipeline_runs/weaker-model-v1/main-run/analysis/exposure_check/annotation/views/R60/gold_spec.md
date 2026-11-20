# Run R60: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.collections.CursorableSubList::insertSequence`
- Gold file in the workspace: `src/java/org/apache/commons/collections/CursorableLinkedList.java` (lines 1394–1400)
- Method the failing test calls (facade): `org.apache.commons.collections.list.SetUniqueList::addAll`
- Failing test: `org.apache.commons.collections.list.TestSetUniqueList::testIntCollectionAddAll`
- Text removed from the gold (the omission): `Object element = it.next();             if (!list.contains(element)) {                 list.add(pos++, element);             }`
- The same place in the variant now reads: `Object element = it.next();             list.add(pos++, element);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1394        public static void insertSequence(List list, int index, Collection coll) {
 1395            int pos = index;
 1396            for (Iterator it = coll.iterator(); it.hasNext();) {
 1397 >>             Object element = it.next();
 1398 >>             list.add(pos++, element);
 1399            }
 1400        }
```
