# Run R19: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.joda.time.LocalDate::productOf`
- Gold file in the workspace: `src/main/java/org/joda/time/LocalDate.java` (lines 1086–1094)
- Method the failing test calls (facade): `org.joda.time.field.FieldUtils::safeMultiply`
- Failing test: `org.joda.time.field.TestFieldUtils::testSafeMultiplyLongLong`
- Text removed from the gold (the omission): `if (total / larger != smaller                 || smaller == Long.MIN_VALUE && larger == -1) {`
- The same place in the variant now reads: `if (total / larger != smaller) {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 1086        public static long productOf(long val1, long val2) {
 1087            final long smaller = Math.min(val1, val2);
 1088            final long larger = Math.max(val1, val2);
 1089            final long total = smaller * larger;
 1090 >>         if (total / larger != smaller) {
 1091                throw new ArithmeticException("Multiplication overflows a long: " + val1 + " * " + val2);
 1092            }
 1093            return total;
 1094        }
```
