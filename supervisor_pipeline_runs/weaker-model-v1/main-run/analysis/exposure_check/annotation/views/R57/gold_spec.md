# Run R57: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.jsoup.nodes.Node::appendUnescaped`
- Gold file in the workspace: `src/main/java/org/jsoup/nodes/Node.java` (lines 100–107)
- Method the failing test calls (facade): `org.jsoup.parser.TokenQueue::unescape`
- Failing test: `org.jsoup.parser.TokenQueueTest::unescape`
- Text removed from the gold (the omission): `for (int esc = text.indexOf('\\'); esc != -1; esc = text.indexOf('\\', esc + 1)) {             if (esc > 0 && text.charAt(esc - 1) == '\\') continue;             accum.append(text, start, esc);`
- The same place in the variant now reads: `for (int esc = text.indexOf('\\'); esc != -1; esc = text.indexOf('\\', esc + 1)) {             accum.append(text, start, esc);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  100        public static void appendUnescaped(StringBuilder accum, String text) {
  101            int start = 0;
  102 >>         for (int esc = text.indexOf('\\'); esc != -1; esc = text.indexOf('\\', esc + 1)) {
  103 >>             accum.append(text, start, esc);
  104                start = esc + 1;
  105            }
  106            accum.append(text, start, text.length());
  107        }
```
