# Run R21: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang3.time.DateUtils::properFractionString`
- Gold file in the workspace: `src/main/java/org/apache/commons/lang3/time/DateUtils.java` (lines 1777–1787)
- Method the failing test calls (facade): `org.apache.commons.lang3.math.Fraction::toProperString`
- Failing test: `org.apache.commons.lang3.math.FractionTest::testToProperString`
- Text removed from the gold (the omission): `int remainder = numerator % denominator;         if (remainder < 0) {             remainder = -remainder;         }`
- The same place in the variant now reads: `int remainder = numerator % denominator;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1777        public static String properFractionString(int numerator, int denominator) {
 1778            int whole = numerator / denominator;
 1779 >>         int remainder = numerator % denominator;
 1780            if (remainder == 0) {
 1781                return Integer.toString(whole);
 1782            }
 1783            if (whole == 0) {
 1784                return numerator + "/" + denominator;
 1785            }
 1786            return whole + " " + remainder + "/" + denominator;
 1787        }
```
