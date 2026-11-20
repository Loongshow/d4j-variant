# Run R15: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.math.linear.BlockRealMatrix::rotationEntry`
- Gold file in the workspace: `src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java` (lines 1232–1238)
- Method the failing test calls (facade): `org.apache.commons.math.geometry.euclidean.threed.Rotation::getMatrix`
- Failing test: `org.apache.commons.math.geometry.euclidean.threed.RotationTest::testMatrix`
- Text removed from the gold (the omission): `return 2.0 * (v[row] * v[column] + ((column == (row + 1) % 3) ? twist : -twist));`
- The same place in the variant now reads: `return 2.0 * (v[row] * v[column] + twist);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1232        public static double rotationEntry(final double q0, final double[] v, final int row, final int column) {
 1233            if (row == column) {
 1234                return 2.0 * (q0 * q0 + v[row] * v[row]) - 1.0;
 1235            }
 1236            final double twist = q0 * v[3 - row - column];
 1237 >>         return 2.0 * (v[row] * v[column] + twist);
 1238        }
```
