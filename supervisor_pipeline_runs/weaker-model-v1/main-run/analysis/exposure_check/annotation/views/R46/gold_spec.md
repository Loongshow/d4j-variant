# Run R46: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.jsoup.select.Elements::firstTagged`
- Gold file in the workspace: `src/main/java/org/jsoup/select/Elements.java` (lines 428–436)
- Method the failing test calls (facade): `org.jsoup.nodes.Document::title`
- Failing test: `org.jsoup.nodes.DocumentTest::testTitles`
- Text removed from the gold (the omission): `return candidate;             candidates.addAll(i + 1, candidate.children());`
- The same place in the variant now reads: `return candidate;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  428        public static Element firstTagged(Element root, String tagName) {
  429            Elements candidates = root.children();
  430            for (int i = 0; i < candidates.size(); i++) {
  431                Element candidate = candidates.get(i);
  432                if (candidate.tagName().equals(tagName))
  433 >>                 return candidate;
  434            }
  435            return null;
  436        }
```
