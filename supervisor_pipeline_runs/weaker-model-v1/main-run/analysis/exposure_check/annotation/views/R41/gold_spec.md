# Run R41: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.collections4.map.AbstractHashedMap::removeAllBut`
- Gold file in the workspace: `src/main/java/org/apache/commons/collections4/map/AbstractHashedMap.java` (lines 377–383)
- Method the failing test calls (facade): `org.apache.commons.collections4.list.SetUniqueList::retainAll`
- Failing test: `org.apache.commons.collections4.list.SetUniqueListTest::testCollectionRetainAll`
- Text removed from the gold (the omission): `if (!kept.contains(list.get(i))) {                 list.remove(i);                 i--;`
- The same place in the variant now reads: `if (!kept.contains(list.get(i))) {                 list.remove(i);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  377        public static <E> void removeAllBut(final List<E> list, final Set<?> kept) {
  378            for (int i = 0; i < list.size(); i++) {
  379 >>             if (!kept.contains(list.get(i))) {
  380 >>                 list.remove(i);
  381                }
  382            }
  383        }
```
