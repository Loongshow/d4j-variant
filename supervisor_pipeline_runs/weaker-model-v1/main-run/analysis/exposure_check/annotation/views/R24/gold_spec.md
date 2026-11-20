# Run R24: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.math.linear.BlockFieldMatrix::addByBlocks`
- Gold file in the workspace: `src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java` (lines 1214–1223)
- Method the failing test calls (facade): `org.apache.commons.math.linear.ArrayRealVector::mapAddToSelf`
- Failing test: `org.apache.commons.math.linear.ArrayRealVectorTest::testMapFunctions`
- Text removed from the gold (the omission): `final int blockCount = (column.length + BLOCK_SIZE - 1) / BLOCK_SIZE;`
- The same place in the variant now reads: `final int blockCount = column.length / BLOCK_SIZE;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1214        public static void addByBlocks(final double[] column, final double d) {
 1215 >>         final int blockCount = column.length / BLOCK_SIZE;
 1216            for (int iBlock = 0; iBlock < blockCount; ++iBlock) {
 1217                final int pStart = iBlock * BLOCK_SIZE;
 1218                final int height = (iBlock == blockCount - 1) ? column.length - pStart : BLOCK_SIZE;
 1219                for (int p = pStart; p < pStart + height; ++p) {
 1220                    column[p] += d;
 1221                }
 1222            }
 1223        }
```
