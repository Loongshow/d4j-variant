# Run R40: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.lang3.ArrayUtils::anyCharFound`
- Gold file in the workspace: `src/main/java/org/apache/commons/lang3/ArrayUtils.java` (lines 2814–2826)
- Method the failing test calls (facade): `org.apache.commons.lang3.StringUtils::containsAny`
- Failing test: `org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsAnyStringWithSupplementaryChars`
- Text removed from the gold (the omission): `if (searchChars[k] == ch                         && (i + 1 == csLength || k + 1 == searchLength || !Character.isHighSurrogate(ch) || searchChars[k + 1] == cs.charAt(i + 1))) {`
- The same place in the variant now reads: `if (searchChars[k] == ch) {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
 2814        public static boolean anyCharFound(CharSequence cs, char[] searchChars) {
 2815            final int csLength = cs.length();
 2816            final int searchLength = searchChars.length;
 2817            for (int i = 0; i < csLength; i++) {
 2818                final char ch = cs.charAt(i);
 2819                for (int k = 0; k < searchLength; k++) {
 2820 >>                 if (searchChars[k] == ch) {
 2821                        return true;
 2822                    }
 2823                }
 2824            }
 2825            return false;
 2826        }
```
