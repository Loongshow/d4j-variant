# Run R31: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang3.time.DateUtils::valueOfDigits`
- Gold file in the workspace: `src/main/java/org/apache/commons/lang3/time/DateUtils.java` (lines 1606–1617)
- Method the failing test calls (facade): `org.apache.commons.lang3.math.NumberUtils::createInteger`
- Failing test: `org.apache.commons.lang3.math.NumberUtilsTest::testCreateNumber`
- Text removed from the gold (the omission): `if (value < ((negative ? Integer.MIN_VALUE : -Integer.MAX_VALUE) + digit) / radix) {                 throw new NumberFormatException("For input string: \"" + digits + "\"");             }             value = value * radix - digit;`
- The same place in the variant now reads: `value = value * radix - digit;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1606        public static int valueOfDigits(String digits, int radix, boolean negative) {
 1607            final int length = digits.length();
 1608            int value = 0;
 1609            for (int i = 0; i < length; i++) {
 1610                final int digit = Character.digit(digits.charAt(i), radix);
 1611                if (digit < 0) {
 1612                    throw new NumberFormatException("For input string: \"" + digits + "\"");
 1613                }
 1614 >>             value = value * radix - digit;
 1615            }
 1616            return negative ? value : -value;
 1617        }
```
