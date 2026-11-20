# Run R47: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.math.optimization.direct.CMAESOptimizer::digitExponent`
- Gold file in the workspace: `src/main/java/org/apache/commons/math/optimization/direct/CMAESOptimizer.java` (lines 351–354)
- Method the failing test calls (facade): `org.apache.commons.math.dfp.Dfp::log10`
- Failing test: `org.apache.commons.math.dfp.DfpTest::testLog10`
- Text removed from the gold (the omission): `int exponent = ((31 - Integer.numberOfLeadingZeros(value)) * 1233) >> 12;         if (value >= MathUtils.pow(10, exponent + 1)) {             exponent++;         }         return exponent;`
- The same place in the variant now reads: `int exponent = ((31 - Integer.numberOfLeadingZeros(value)) * 1233) >> 12;         return exponent;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  351        public static int digitExponent(final int value) {
  352 >>         int exponent = ((31 - Integer.numberOfLeadingZeros(value)) * 1233) >> 12;
  353 >>         return exponent;
  354        }
```
