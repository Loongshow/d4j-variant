# Run R28: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.collections.CursorableSubList::indexOfSlot`
- Gold file in the workspace: `src/java/org/apache/commons/collections/CursorableLinkedList.java` (lines 1310–1317)
- Method the failing test calls (facade): `org.apache.commons.collections.map.Flat3Map::containsKey`
- Failing test: `org.apache.commons.collections.map.TestFlat3Map::testSerialisation2`
- Text removed from the gold (the omission): `if (hashes[slot] == hash && (keys[slot] == key || (key != null && key.equals(keys[slot])))) {`
- The same place in the variant now reads: `if (hashes[slot] == hash && keys[slot] == key) {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1310        public static int indexOfSlot(Object key, int hash, Object[] keys, int[] hashes, int count) {
 1311            for (int slot = 0; slot < count; slot++) {
 1312 >>             if (hashes[slot] == hash && keys[slot] == key) {
 1313                    return slot;
 1314                }
 1315            }
 1316            return -1;
 1317        }
```
