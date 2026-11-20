# Run R36: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.math.linear.BlockFieldMatrix::addToEntries`
- Gold file in the workspace: `src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java` (lines 297–309)
- Method the failing test calls (facade): `org.apache.commons.math.linear.OpenMapRealVector::mapAddToSelf`
- Failing test: `org.apache.commons.math.linear.SparseRealVectorTest::testMapFunctions`
- Text removed from the gold (the omission): `if (v.getEntry(i) == 0 && !held[i]) {`
- The same place in the variant now reads: `if (v.getEntry(i) == 0) {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  297        public static void addToEntries(final RealVector v, final boolean[] held, final double d) {
  298            final int n = v.getDimension();
  299            for (int i = 0; i < n; i++) {
  300                if (held[i]) {
  301                    v.setEntry(i, v.getEntry(i) + d);
  302                }
  303            }
  304            for (int i = 0; i < n; i++) {
  305 >>             if (v.getEntry(i) == 0) {
  306                    v.setEntry(i, d);
  307                }
  308            }
  309        }
```
