# Run R10: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.collections4.map.AbstractHashedMap::appendElements`
- Gold file in the workspace: `src/main/java/org/apache/commons/collections4/map/AbstractHashedMap.java` (lines 378–391)
- Method the failing test calls (facade): `org.apache.commons.collections4.list.SetUniqueList::setUniqueList`
- Failing test: `org.apache.commons.collections4.list.SetUniqueListTest::testFactory`
- Text removed from the gold (the omission): `if (existing == element                         || existing != null && existing.equals(element)) {`
- The same place in the variant now reads: `if (existing == element) {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  378        public static <E> void appendElements(final Collection<? extends E> elements, final List<E> list) {
  379            for (final E element : elements) {
  380                boolean present = false;
  381                for (final E existing : list) {
  382 >>                 if (existing == element) {
  383                        present = true;
  384                        break;
  385                    }
  386                }
  387                if (!present) {
  388                    list.add(element);
  389                }
  390            }
  391        }
```
