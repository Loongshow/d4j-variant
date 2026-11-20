# Run R52: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.jsoup.nodes.Node::appendUnescaped`
- Gold file in the workspace: `src/main/java/org/jsoup/nodes/Node.java` (lines 246–255)
- Method the failing test calls (facade): `org.jsoup.parser.TokenQueue::unescape`
- Failing test: `org.jsoup.parser.TokenQueueTest::unescape`
- Text removed from the gold (the omission): `if (chars[i] == '\\'                     && (i == 0 || chars[i - 1] != '\\')) {`
- The same place in the variant now reads: `if (chars[i] == '\\') {`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  246        public static void appendUnescaped(char[] chars, StringBuilder accum) {
  247            int start = 0;
  248            for (int i = 0; i < chars.length; i++) {
  249 >>             if (chars[i] == '\\') {
  250                    accum.append(chars, start, i - start);
  251                    start = i + 1;
  252                }
  253            }
  254            accum.append(chars, start, chars.length - start);
  255        }
```
