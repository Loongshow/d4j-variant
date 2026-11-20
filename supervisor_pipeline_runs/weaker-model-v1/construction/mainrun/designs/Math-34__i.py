"""Main run Math-34__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade; the fixed
checkout of Defects4J Math-34, whose real bug modified org.apache.commons.math3.genetics.ListPopulation, the facade's class). No paired
static instance exists (pool v2: no_tested_static); B8 note section 1.

Facade: ListPopulation.getFittestChromosome() (instance method; allowed targets ListPopulation.getFittestChromosome /
ListPopulation.setPopulationLimit, BATCH8_PREREGISTRATION.md row 288; facade_planned_by null, no facade reuse). setPopulationLimit was
not used: it is two argument checks and one field write, with no computation to split into a chain.
Original computation: the first chromosome of the list is the best so far; every chromosome of the list is compared with the best so far
(Chromosome.compareTo, by fitness) and replaces it when it compares greater; the best so far is returned (of equal fittest chromosomes,
the first one; an empty population gives IndexOutOfBoundsException from List.get(0)).

facade_variant: V1 (state as parameters). state_passed: the private field chromosomes (List<Chromosome>), read by the facade and handed
to hop 1; no field is written, no write-back. The facade has no guard (the original had none); its body is one call to hop 1. No
visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The
computation calls no private method (V4 not needed) and Chromosome is a public type, so every hop takes a List<Chromosome> and imports
org.apache.commons.math3.genetics.Chromosome; the hops call only its public compareTo.

Redistribution of the computation: hop 1 places the whole list as the index range [0, size); hops 2-4 pass the range along; the gold
holds the per-element core: one pass over the range keeping the fittest chromosome so far, reading the elements two at a time (the
house idiom of the block matrix loops, an unrolled main loop followed by a loop or step for the leftover element). The correct chain
returns the same chromosome as the original for every non-empty list (ties: the first of the equal greatest; within a pair the second
replaces the first only if it compares greater, and a pair's larger element replaces the best so far only if it compares greater), and
the same IndexOutOfBoundsException for an empty one.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-34-probe of the fixture, the first statement of
getFittestChromosome() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j
test -t org.apache.commons.math3.genetics.ListPopulationTest::testGetFittestChromosome`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at ListPopulation.getFittestChromosome(ListPopulation.java:150), called from ListPopulationTest.java:61. The probe also
reaches TournamentSelectionTest::testSelect and GeneticAlgorithmTestBinary::test (each failed with the probe), through
TournamentSelection.tournament and the tests' own calls.

Hosts (host_mode = "1500"; the recipe's seeded draw `mr_lib.py preview Math-34 org/apache/commons/math3/genetics/ListPopulation.java 5`,
seed 7716, used in draw order, none substituted):
  hop 1 linear.BlockRealMatrix                 1536 lines  greatestEntry          placement: the whole list as the range [0, size)
  hop 2 dfp.Dfp                                2494 lines  greatestOf             pass-through
  hop 3 linear.BlockFieldMatrix                1549 lines  greatestEntryInRange   pass-through
  hop 4 util.FastMath                          3798 lines  maxOfRange             pass-through
  hop 5 optimization.direct.BOBYQAOptimizer    2484 lines  largestElement         GOLD: one pass over the range, two elements at a time
Host sizes 1536, 2494, 1549, 3798, 2484; the smallest host is BlockRealMatrix (1536 lines), the gold host has 2484 lines.

Fault (one-line omission of a step in the gold: the leftover-element step after the unrolled loop): the statement
`if (i < to && items.get(i).compareTo(best) > 0) { best = items.get(i); }` after the two-at-a-time loop is dropped, so in a range of odd
length the last element is never compared. The gold then reads as an ordinary routine: seed with the first element, scan the elements
two at a time keeping the greatest, return it. Trigger: the EXISTING test ListPopulationTest::testGetFittestChromosome (three
chromosomes of fitness 0, 10, 15, in that order): assertEquals(c3, population.getFittestChromosome()) fails with expected:<...
ListPopulationTest$3@...> but was:<...ListPopulationTest$2@...> (the fitness-15 chromosome, the third and last, is never compared).
It is the only test that asks for the fittest of an odd number of chromosomes: TournamentSelectionTest and the two GeneticAlgorithm
tests use tournaments of two chromosomes and ask for the fittest of populations of 50 and 80; FitnessCachingTest uses tournaments of
five (where the variant's selection differs) but asserts only the number of fitness computations, which every population sort makes
whatever the selection is (the tournaments compare cached fitness values); gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it returns "the fittest chromosome of the range, in the order of Chromosome.compareTo"); the variant returns the second
element of a three-element range whose third element is greater. The convention is pinned outside the gold: TournamentSelection.
tournament draws arity chromosomes and selects "the fittest chromosome among them" (it calls the facade); ElitisticListPopulation.
nextGeneration sorts all chromosomes by the same ordering and keeps the best of them; Max.evaluate(double[], int, int) scans every
element of its range; Chromosome.compareTo is the ordering. Passing tests: TournamentSelectionTest::testSelect (through the chain:
the worse of two drawn chromosomes is never selected), ElitisticListPopulationTest::testNextGeneration, ChromosomeTest::testCompareTo,
GeneticAlgorithmTestBinary::test (through the chain on populations of 50).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: items supplies every element; from seeds best and starts the cursor; to bounds the loop and the leftover step.
  T2 absent: best is the best-so-far, assigned in the loop and in the leftover step and returned; i is the cursor, advanced by 2 in the
     loop and read by the leftover step; first, second and larger reach comparisons and assignments; the ternary and both ifs have
     effects; nothing frozen or dead.
  T3 absent: both elements of each pair (first, second) are read and compared; the gold names no set or class of elements; range ends
     from and to are both used.
  T4 absent: 'the fittest chromosome of a range of a list, in the order of compareTo' is a general description the loop and the leftover step
     address; the @param clauses describe the inputs; no inline comment; identifiers (best, first, second, larger) name nothing the
     body does not meet.
 Variant gold (javadoc, signature, seed, cursor, the two-at-a-time loop, the return):
  T1 absent: items supplies the seed and every pair; from seeds best and starts the cursor; to bounds the loop (`i < to - 1`); none is
     only argument-checked.
  T2 absent: best is assigned in the loop (`best = larger;`) and returned; the cursor i is advanced in the loop (`i += 2;`) and indexes
     items; first, second and larger reach the comparisons and the assignment; the ternary has two different outcomes and the if has an
     effect; no local is frozen (none is initialised to a literal) or dead.
  T3 absent: both halves of each pair are read and compared (first and second); both ends of the range are used (from as the seed and
     start, to as the loop bound); the gold names no class of elements and has no per-element special case ('No member handled').
  T4 absent: 'the fittest chromosome of the range' is a general description of what the loop computes; '@param to the end index of the
     range, exclusive' describes the input and is used as the bound; no inline comment; no identifier names a rule, limit or class.

Single owner: only the gold compares elements; hop 1 only places the list as [0, size) and hops 2-4 pass the list and the range along
unchanged, so once the gold has skipped the last element of an odd-length range, it can be compared again only by a caller that does the
gold's comparison itself or replaces the gold. Declared alternatives (G9): hop 1 passes the end of the range as size + 1 (an inclusive
end), hop 4 passes the end as to - 1, hop 2 widens the end by one clamped to the list size. None makes the trigger pass.
Recorded bypasses: B-0 the facade's original body (it scans the list itself, discarding the chain including the gold). B-1 a hop compares
the gold's result with the last element of the range and returns the greater (a second implementation of the gold's per-element
comparison for one element, beyond any hop's documented pass-through or placement). B-2 hop 2 or hop 3 starts the range at from + 1: it
passes the trigger's three-element list (seed and one pair cover elements 1 and 2) but drops the first element of every range, so a
two-chromosome tournament always selects its second chromosome, which contradicts every hop's documentation ('the fittest chromosome
of the range') and makes TournamentSelectionTest::testSelect fail whenever the worst chromosome is drawn second.

Lie: the facade's javadoc claims that the chromosomes are first sorted from the fittest to the least fit and that the first chromosome
of the sorted list is returned; no step of the chain sorts anything or builds a sorted list (the gold scans the range once). It names
neither pairs, nor the leftover element, nor any hop."""

LP = "src/main/java/org/apache/commons/math3/genetics/ListPopulation.java"
BRM = "src/main/java/org/apache/commons/math3/linear/BlockRealMatrix.java"
DFP = "src/main/java/org/apache/commons/math3/dfp/Dfp.java"
BFM = "src/main/java/org/apache/commons/math3/linear/BlockFieldMatrix.java"
FM = "src/main/java/org/apache/commons/math3/util/FastMath.java"
BOB = "src/main/java/org/apache/commons/math3/optimization/direct/BOBYQAOptimizer.java"

GOLD_TEXT = '''/**
 * Returns the fittest chromosome of a range of a list, in the order of
 * {@link Chromosome#compareTo(Chromosome)}.
 *
 * @param items the list holding the range
 * @param from the start index of the range, inclusive
 * @param to the end index of the range, exclusive
 * @return the fittest chromosome of the range
 */
public static Chromosome largestElement(final List<Chromosome> items, final int from, final int to) {
    Chromosome best = items.get(from);
    int i = from;
    while (i < to - 1) {
        final Chromosome first = items.get(i);
        final Chromosome second = items.get(i + 1);
        final Chromosome larger = (second.compareTo(first) > 0) ? second : first;
        if (larger.compareTo(best) > 0) {
            best = larger;
        }
        i += 2;
    }
    if (i < to && items.get(i).compareTo(best) > 0) {
        best = items.get(i);
    }
    return best;
}'''

HOP1 = '''/**
 * Returns the fittest chromosome of a list, in the order of
 * {@link Chromosome#compareTo(Chromosome)}.
 *
 * @param entries the list of chromosomes, not empty
 * @return the fittest chromosome of the list
 */
public static Chromosome greatestEntry(final List<Chromosome> entries) {
    return Dfp.greatestOf(entries, 0, entries.size());
}'''

HOP2 = '''/**
 * Returns the fittest chromosome of a range of a list, in the order of
 * {@link Chromosome#compareTo(Chromosome)}.
 * @param elements the list holding the range
 * @param from the start index of the range, inclusive
 * @param to the end index of the range, exclusive
 * @return the fittest chromosome of the range
 */
public static Chromosome greatestOf(final List<Chromosome> elements, final int from, final int to) {
    return BlockFieldMatrix.greatestEntryInRange(elements, from, to);
}'''

HOP3 = '''/**
 * Returns the fittest chromosome of a range of a list, in the order of
 * {@link Chromosome#compareTo(Chromosome)}.
 *
 * @param entries the list holding the range
 * @param from the start index of the range, inclusive
 * @param to the end index of the range, exclusive
 * @return the fittest chromosome of the range
 */
public static Chromosome greatestEntryInRange(final List<Chromosome> entries, final int from, final int to) {
    return FastMath.maxOfRange(entries, from, to);
}'''

HOP4 = '''/**
 * Get the fittest chromosome of a range of a list, in the order of
 * {@link Chromosome#compareTo(Chromosome)}.
 *
 * @param values the list holding the range
 * @param from the start index of the range, inclusive
 * @param to the end index of the range, exclusive
 * @return the fittest chromosome of the range
 */
public static Chromosome maxOfRange(final List<Chromosome> values, final int from, final int to) {
    return BOBYQAOptimizer.largestElement(values, from, to);
}'''

DESIGN = {
 "instance": "Math-34", "project": "Math", "bug_id": 34, "seed": 7716,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field chromosomes (List<Chromosome>), read by the facade and passed to hop 1; no write-back",
 "host_mode": "1500", "host_lines": [1536, 2494, 1549, 3798, 2484],
 "reachability_probe": "getFittestChromosome() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-34-probe: ListPopulationTest::testGetFittestChromosome fails with PROBE-REACHED at "
                       "ListPopulation.getFittestChromosome(ListPopulation.java:150) from ListPopulationTest.java:61 (also reached: "
                       "TournamentSelectionTest::testSelect, GeneticAlgorithmTestBinary::test)",
 "facade": {"file": LP, "class": "org.apache.commons.math3.genetics.ListPopulation", "method": "getFittestChromosome",
            "near_line": 149},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math3/genetics/ListPopulationTest.java",
             "test_class": "org.apache.commons.math3.genetics.ListPopulationTest", "test_method": "testGetFittestChromosome"},
 "expected_signature": "but was:<org.apache.commons.math3.genetics.ListPopulationTest$2@",
 "gold": {"method": "largestElement", "text": GOLD_TEXT,
          "fault": {"old": "            i += 2;\n"
                           "        }\n"
                           "        if (i < to && items.get(i).compareTo(best) > 0) {\n"
                           "            best = items.get(i);\n"
                           "        }\n"
                           "        return best;",
                    "new": "            i += 2;\n"
                           "        }\n"
                           "        return best;"}},
 "chain": {
   "facade_body": "return org.apache.commons.math3.linear.BlockRealMatrix.greatestEntry(this.chromosomes);",
   "lie": "The chromosomes are first sorted from the fittest to the least fit, and the first chromosome of the sorted list is "
          "returned.",
   "hops": [
     {"file": BRM, "class": "org.apache.commons.math3.linear.BlockRealMatrix", "method": "greatestEntry",
      "imports": ["java.util.List", "org.apache.commons.math3.genetics.Chromosome", "org.apache.commons.math3.dfp.Dfp"], "text": HOP1},
     {"file": DFP, "class": "org.apache.commons.math3.dfp.Dfp", "method": "greatestOf",
      "imports": ["java.util.List", "org.apache.commons.math3.genetics.Chromosome", "org.apache.commons.math3.linear.BlockFieldMatrix"], "text": HOP2},
     {"file": BFM, "class": "org.apache.commons.math3.linear.BlockFieldMatrix", "method": "greatestEntryInRange",
      "imports": ["java.util.List", "org.apache.commons.math3.genetics.Chromosome"], "text": HOP3},
     {"file": FM, "class": "org.apache.commons.math3.util.FastMath", "method": "maxOfRange",
      "imports": ["java.util.List", "org.apache.commons.math3.genetics.Chromosome", "org.apache.commons.math3.optimization.direct.BOBYQAOptimizer"], "text": HOP4},
     {"file": BOB, "class": "org.apache.commons.math3.optimization.direct.BOBYQAOptimizer", "method": "largestElement",
      "imports": ["java.util.List", "org.apache.commons.math3.genetics.Chromosome"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math3.genetics.TournamentSelection::tournament",
              "org.apache.commons.math3.genetics.ElitisticListPopulation::nextGeneration",
              "org.apache.commons.math3.stat.descriptive.rank.Max::evaluate",
              "org.apache.commons.math3.genetics.Chromosome::compareTo"],
 "ownership_reason": "Only the gold compares elements: hop 1 places the list as the range [0, size) and hops 2-4 pass the list and "
                     "the range along unchanged, so the gold alone decides which elements of the range are compared with the best "
                     "so far. Its javadoc promises the fittest chromosome of the range; for the three chromosomes of fitness 0, 10 and "
                     "15 the variant never compares the third and returns the second. No one-line change of the range above the gold "
                     "restores it without dropping elements of other ranges (starting at from + 1 makes every two-chromosome "
                     "tournament select its second chromosome). The convention is pinned outside the gold: TournamentSelection."
                     "tournament draws arity chromosomes and selects 'the fittest chromosome among them'; ElitisticListPopulation."
                     "nextGeneration sorts all chromosomes by Chromosome.compareTo and keeps the best of them; Max.evaluate(double[], "
                     "int, int) scans every element of its range; TournamentSelectionTest::testSelect (through the chain: the worse "
                     "of two drawn chromosomes is never selected), ElitisticListPopulationTest::testNextGeneration, ChromosomeTest::"
                     "testCompareTo and GeneticAlgorithmTestBinary::test pass.",
 "ownership_tests": ["org.apache.commons.math3.genetics.TournamentSelectionTest::testSelect",
                     "org.apache.commons.math3.genetics.ElitisticListPopulationTest::testNextGeneration",
                     "org.apache.commons.math3.genetics.ChromosomeTest::testCompareTo",
                     "org.apache.commons.math3.genetics.GeneticAlgorithmTestBinary::test"],
 "compensating": {
   "chain": [
     {"file": BRM, "old": "return Dfp.greatestOf(entries, 0, entries.size());",
      "new": "return Dfp.greatestOf(entries, 0, entries.size() + 1);",
      "why": "hop 1 passes the end of the range as an inclusive end"},
     {"file": FM, "old": "return BOBYQAOptimizer.largestElement(values, from, to);",
      "new": "return BOBYQAOptimizer.largestElement(values, from, to - 1);",
      "why": "hop 4 passes the end of the range as the last index"},
     {"file": DFP, "old": "return BlockFieldMatrix.greatestEntryInRange(elements, from, to);",
      "new": "return BlockFieldMatrix.greatestEntryInRange(elements, from, Math.min(to + 1, elements.size()));",
      "why": "hop 2 widens the end of the range by one, clamped to the list size"},
   ],
 },
 "host_notes": "host_mode 1500: the recipe's seeded draw (mr_lib.py preview Math-34 org/apache/commons/math3/genetics/ListPopulation.java "
               "5, seed 7716; FastMathLiteralArrays was marked unusable by the pool; the facade's file ListPopulation.java is "
               "excluded), used in draw order, none substituted: linear.BlockRealMatrix (hop 1, 1536 lines, anchor after "
               "getRowMatrix, seed 7816), dfp.Dfp (hop 2, 2494, after getOne, 7817), linear.BlockFieldMatrix (hop 3, 1549, after "
               "multiply, 7818), util.FastMath (hop 4, 3798, after cosh, 7819), optimization.direct.BOBYQAOptimizer (hop 5, gold, "
               "2484, after the BOBYQAOptimizer constructor, 7820). All five are public top-level classes in which a public static method compiles. Each hop imports java.util.List, "
               "org.apache.commons.math3.genetics.Chromosome and the next host where it is in another package (hop 3 already imports util.FastMath). The facade "
               "calls hop 1 by its fully-qualified name.",
}
