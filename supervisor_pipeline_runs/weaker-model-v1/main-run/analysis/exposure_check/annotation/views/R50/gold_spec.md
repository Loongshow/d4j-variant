# Run R50: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `com.fasterxml.jackson.core.json.UTF8JsonGenerator::expandedBufferLength`
- Gold file in the workspace: `src/main/java/com/fasterxml/jackson/core/json/UTF8JsonGenerator.java` (lines 579–585)
- Method the failing test calls (facade): `com.fasterxml.jackson.core.util.TextBuffer::expandCurrentSegment`
- Failing test: `com.fasterxml.jackson.core.util.TestTextBuffer::testExpand`
- Text removed from the gold (the omission): `grown = Math.max(threshold, length + (length >> 2));`
- The same place in the variant now reads: `grown = threshold;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  579        public static int expandedBufferLength(final int length, final int threshold) {
  580            int grown = length + (length >> 1);
  581            if (grown > threshold) {
  582 >>             grown = threshold;
  583            }
  584            return grown;
  585        }
```
