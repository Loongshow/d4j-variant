# Run R48: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.collections4.map.AbstractHashedMap::addAllEntries`
- Gold file in the workspace: `src/main/java/org/apache/commons/collections4/map/AbstractHashedMap.java` (lines 1003–1007)
- Method the failing test calls (facade): `org.apache.commons.collections4.map.MultiValueMap::putAll`
- Failing test: `org.apache.commons.collections4.map.MultiValueMapTest::testPutAll_Map1`
- Text removed from the gold (the omission): `for (final Map.Entry<? extends K, ?> entry : map.entrySet()) {             if (map instanceof org.apache.commons.collections4.MultiMap) {                 target.putAll(entry.getKey(), (Collection<V>) entry.getValue());             } else {                 target.put(entry.getKey(), entry.getValue());             }         }`
- The same place in the variant now reads: `for (final Map.Entry<? extends K, ?> entry : map.entrySet()) {             target.put(entry.getKey(), entry.getValue());         }`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1003        public static <K, V> void addAllEntries(final MultiValueMap<K, V> target, final Map<? extends K, ?> map) {
 1004 >>         for (final Map.Entry<? extends K, ?> entry : map.entrySet()) {
 1005 >>             target.put(entry.getKey(), entry.getValue());
 1006            }
 1007        }
```
