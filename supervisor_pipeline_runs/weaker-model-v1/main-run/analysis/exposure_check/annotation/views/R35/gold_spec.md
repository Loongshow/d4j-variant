# Run R35: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.math3.linear.BlockRealMatrix::decadeOf`
- Gold file in the workspace: `src/main/java/org/apache/commons/math3/linear/BlockRealMatrix.java` (lines 1430–1433)
- Method the failing test calls (facade): `org.apache.commons.math3.dfp.Dfp::log10`
- Failing test: `org.apache.commons.math3.dfp.DfpTest::testLog10`
- Text removed from the gold (the omission): `return limb > FastMath.pow(10, decade + 1) ? decade + 1 : decade;`
- The same place in the variant now reads: `return decade;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1430        public static int decadeOf(final int limb) {
 1431            final int decade = (31 - Integer.numberOfLeadingZeros(FastMath.max(limb, 1))) * 1233 >> 12;
 1432 >>         return decade;
 1433        }
```
