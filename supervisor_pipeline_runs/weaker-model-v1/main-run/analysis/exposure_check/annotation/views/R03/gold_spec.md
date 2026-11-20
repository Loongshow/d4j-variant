# Run R03: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.math3.optimization.direct.BOBYQAOptimizer::largestElement`
- Gold file in the workspace: `src/main/java/org/apache/commons/math3/optimization/direct/BOBYQAOptimizer.java` (lines 244–257)
- Method the failing test calls (facade): `org.apache.commons.math3.genetics.ListPopulation::getFittestChromosome`
- Failing test: `org.apache.commons.math3.genetics.ListPopulationTest::testGetFittestChromosome`
- Text removed from the gold (the omission): `i += 2;         }         if (i < to && items.get(i).compareTo(best) > 0) {             best = items.get(i);         }         return best;`
- The same place in the variant now reads: `i += 2;         }         return best;`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  244        public static Chromosome largestElement(final List<Chromosome> items, final int from, final int to) {
  245            Chromosome best = items.get(from);
  246            int i = from;
  247            while (i < to - 1) {
  248                final Chromosome first = items.get(i);
  249                final Chromosome second = items.get(i + 1);
  250                final Chromosome larger = (second.compareTo(first) > 0) ? second : first;
  251                if (larger.compareTo(best) > 0) {
  252                    best = larger;
  253                }
  254 >>             i += 2;
  255            }
  256 >>         return best;
  257        }
```
