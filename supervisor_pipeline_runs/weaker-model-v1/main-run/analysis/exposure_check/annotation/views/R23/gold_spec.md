# Run R23: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `com.fasterxml.jackson.core.json.ReaderBasedJsonParser::grownBufferLength`
- Gold file in the workspace: `src/main/java/com/fasterxml/jackson/core/json/ReaderBasedJsonParser.java` (lines 383–388)
- Method the failing test calls (facade): `com.fasterxml.jackson.core.util.TextBuffer::expandCurrentSegment`
- Failing test: `com.fasterxml.jackson.core.util.TestTextBuffer::testExpand`
- Text removed from the gold (the omission): `int grown = Math.min(byHalf, limit);         if (grown < byHalf) grown = length + (length >> 2);`
- The same place in the variant now reads: `int grown = Math.min(byHalf, limit);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  383        public static int grownBufferLength(int length, int limit)
  384        {
  385            int byHalf = length + (length >> 1);
  386 >>         int grown = Math.min(byHalf, limit);
  387            return grown;
  388        }
```
