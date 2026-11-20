# Run R42: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang3.time.DateUtils::convergentTerms`
- Gold file in the workspace: `src/main/java/org/apache/commons/lang3/time/DateUtils.java` (lines 1777–1817)
- Method the failing test calls (facade): `org.apache.commons.lang3.math.Fraction::getFraction`
- Failing test: `org.apache.commons.lang3.math.FractionTest::testFactory_String_double`
- Text removed from the gold (the omission): `} while (delta1 > delta2                 && denom2 <= 10000                 && denom2 > 0                 && i < 25);`
- The same place in the variant now reads: `} while (delta1 > delta2                 && denom2 > 0                 && i < 25);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1777        public static int[] convergentTerms(double value) {
 1778            int numer0 = 0;  // the pre-previous
 1779            int denom0 = 1;  // the pre-previous
 1780            int numer1 = 1;  // the previous
 1781            int denom1 = 0;  // the previous
 1782            int numer2 = 0;  // the current
 1783            int denom2 = 0;  // the current
 1784            int a1 = (int) value;
 1785            int a2 = 0;
 1786            double x1 = 1;
 1787            double x2 = 0;
 1788            double y1 = value - a1;
 1789            double y2 = 0;
 1790            double delta1, delta2 = Double.MAX_VALUE;
 1791            double fraction;
 1792            int i = 1;
 1793            do {
 1794                delta1 = delta2;
 1795                a2 = (int) (x1 / y1);
 1796                x2 = y1;
 1797                y2 = x1 - a2 * y1;
 1798                numer2 = a1 * numer1 + numer0;
 1799                denom2 = a1 * denom1 + denom0;
 1800                fraction = (double) numer2 / (double) denom2;
 1801                delta2 = Math.abs(value - fraction);
 1802                a1 = a2;
 1803                x1 = x2;
 1804                y1 = y2;
 1805                numer0 = numer1;
 1806                denom0 = denom1;
 1807                numer1 = numer2;
 1808                denom1 = denom2;
 1809                i++;
 1810 >>         } while (delta1 > delta2
 1811 >>                 && denom2 > 0
 1812 >>                 && i < 25);
 1813            if (i == 25) {
 1814                throw new ArithmeticException("Unable to convert double to fraction");
 1815            }
 1816            return new int[] {numer0, denom0};
 1817        }
```
