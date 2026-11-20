# Run R51: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang3.ArrayUtils::randomChars`
- Gold file in the workspace: `src/main/java/org/apache/commons/lang3/ArrayUtils.java` (lines 4399–4421)
- Method the failing test calls (facade): `org.apache.commons.lang3.RandomStringUtils::random`
- Failing test: `org.apache.commons.lang3.RandomStringUtilsTest::testRandomStringUtils`
- Text removed from the gold (the omission): `buffer[count] = ch;                 }             } else {                 count++;             }         }         return new String(buffer);`
- The same place in the variant now reads: `buffer[count] = ch;                 }             }         }         return new String(buffer);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 4399        public static String randomChars(int count, int start, int gap, boolean letters, boolean numbers, Random random) {
 4400            final char[] buffer = new char[count];
 4401            while (count-- != 0) {
 4402                final char ch = (char) (random.nextInt(gap) + start);
 4403                final boolean low = ch >= 56320 && ch <= 57343;
 4404                final boolean high = ch >= 55296 && ch <= 56191;
 4405                if ((letters && Character.isLetter(ch) || numbers && Character.isDigit(ch) || !letters && !numbers)
 4406                        && (ch < 56192 || ch > 56319) && (count > 0 || !low && !high)) {
 4407                    if (low) {
 4408 >>                     buffer[count] = ch;
 4409                        count--;
 4410                        buffer[count] = (char) (55296 + random.nextInt(128));
 4411 >>                 } else if (high) {
 4412                        buffer[count] = (char) (56320 + random.nextInt(128));
 4413                        count--;
 4414 >>                     buffer[count] = ch;
 4415 >>                 } else {
 4416 >>                     buffer[count] = ch;
 4417                    }
 4418                }
 4419            }
 4420 >>         return new String(buffer);
 4421        }
```
