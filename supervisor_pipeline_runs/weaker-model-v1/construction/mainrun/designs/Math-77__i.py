"""Main run Math-77__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug without a static facade; the
fixed checkout of Defects4J Math-77, whose real bug modified ArrayRealVector and OpenMapRealVector; the facade is in ArrayRealVector).
No static pair exists (BUILD_BRIEF_C10I_B8_NOTE.md section 1).

Facade: ArrayRealVector.mapAddToSelf(double) (instance method; allowed targets ArrayRealVector.mapAddToSelf / mapSubtractToSelf /
mapMultiplyToSelf, BATCH8_PREREGISTRATION.md row 299; facade_planned_by null for all three, no facade reuse). mapAddToSelf was chosen
because it is reached by exactly one existing test (see the probe); mapMultiplyToSelf is reached through mapMultiply by production code
(ArrayRealVector.projection, SimplexTableau) and so by many tests, and mapSubtractToSelf carries the same computation as mapAddToSelf.
Original computation: data[i] = data[i] + d for every i in [0, data.length), in place; returns this. AbstractRealVector.mapAdd
(inherited, not overridden) calls copy().mapAddToSelf(d).

facade_variant: V1 (state as parameters). state_passed: the protected field data (the double[] of the entries, updated in place by the
chain) and the scalar d, passed to hop 1; no field is assigned, so there is no write-back; the facade returns this as the original does.
The facade body is one call to hop 1 followed by `return this;` (the original has no guard). No visibility is widened, no type is
added, no signature, modifier, override or throws clause changes, no reflection, no test edit. The facade's javadoc is
`/** {@inheritDoc} */`; the lie sentence is appended to it by the recipe.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-77-probe of the fixture, the first statement of
mapAddToSelf was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.apache.commons.math.linear.ArrayRealVectorTest::testMapFunctions`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
ArrayRealVector.mapAddToSelf(ArrayRealVector.java:347), called from AbstractRealVector.mapAdd(AbstractRealVector.java:150), called from
ArrayRealVectorTest.testMapFunctions(ArrayRealVectorTest.java:756). Full suite with the probe: 1 failing test (testMapFunctions only),
so no other test and no production path used by a test reaches the facade.

Hosts (host_mode = "1500"; `mr_lib.py preview Math-77 org/apache/commons/math/linear/ArrayRealVector.java 5`, seed 3648, draw order
used as drawn, none substituted):
  hop 1 linear.BlockRealMatrix         1687 lines  scalarAddToColumn  pass-through
  hop 2 util.MathUtils                 1663 lines  addToAll           decision: an empty array is left as it is
  hop 3 linear.EigenDecompositionImpl  1915 lines  addToEntries       pass-through
  hop 4 linear.BigMatrixImpl           1506 lines  scalarAddEntries   pass-through
  hop 5 linear.BlockFieldMatrix        1667 lines  addByBlocks        GOLD: the block count, the start and height of each block,
                                                                      and the per-entry addition
Host sizes 1687, 1663, 1915, 1506, 1667; the smallest host is BigMatrixImpl (1506 lines); the gold host has 1667 lines.
The correct configuration gives the original result for every array: the block count is the ceiling of length / BLOCK_SIZE, block i
covers [i * BLOCK_SIZE, i * BLOCK_SIZE + height) with height BLOCK_SIZE except for the last block, which ends at the end of the array, so
every entry is visited exactly once and receives d by the same `+=` the original performs; the empty-array shortcut of hop 2 skips a
loop that would do nothing.

Fault (one-line omission in the gold's block count): the rounding-up term of the block count is dropped
(`final int blockCount = (column.length + BLOCK_SIZE - 1) / BLOCK_SIZE;` becomes `final int blockCount = column.length / BLOCK_SIZE;`).
The gold then reads as the ordinary routine "count the blocks, give the last block the rest of the column": for a column of at least
BLOCK_SIZE (36) entries it still adds d to every entry (the last block takes the remainder), but a column shorter than one block has no
block at all and is left unchanged. Trigger: the EXISTING test ArrayRealVectorTest::testMapFunctions: v1.mapAdd(2.0) on {1, 2, 3}
(through copy().mapAddToSelf) leaves {1, 2, 3}, and assertClose fails with "compare vectors 0 elements differ expected:<3.0> but
was:<1.0>". It is the only test that newly fails: the probe's full-suite run shows that no other test reaches the facade, and the new
hops have no other caller.

The gold's javadoc states the idiomatic contract (a scalar is added to each entry of the column, taken block by block as the rows of
a block matrix are split, block i starting at entry i * BLOCK_SIZE) and is silent on how the blocks are counted; on the trigger the
entries of a 3-entry column receive nothing. The convention (the number of blocks is the length rounded up to whole blocks, the last
block holding what remains) is pinned outside the gold: BlockFieldMatrix.createBlocksLayout and BlockRealMatrix.createBlocksLayout
(`blockRows = (rows + BLOCK_SIZE - 1) / BLOCK_SIZE`, the last block `rows - blockRow * BLOCK_SIZE` high, as in
BlockFieldMatrix.blockHeight), with BlockFieldMatrixTest::testSeveralBlocks (37 x 41: one full and one partial block),
BlockFieldMatrixTest::testDimensions (a matrix smaller than one block) and BlockRealMatrixTest::testSeveralBlocks passing; and the
step "every entry receives d" by the intact OpenMapRealVector.mapAddToSelf (setEntry(i, getEntry(i) + d) for every i) and
ArrayRealVector.mapSubtractToSelf, with SparseRealVectorTest::testMapFunctions passing.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: column gives the block count, the last block's height and every updated entry; d is added to every visited entry; no
     argument check.
  T2 absent: blockCount bounds the block loop and decides the last block; iBlock and p are advanced by their loops; pStart and height
     bound the entry loop; the ternary's branches give different heights (column.length - pStart vs BLOCK_SIZE).
  T3 absent: both ends of each block are computed (pStart and pStart + height, none clamped); the last block and the other blocks
     both get a height; no enum, type code, named format or named value class is involved.
  T4 absent: 'Adds a scalar to each entry of a column, block by block' is a general description met by the loops; 'block i starts at
     entry i * BLOCK_SIZE' is met by pStart; the @param clauses name no rule.
 Variant gold (javadoc, signature, `blockCount = column.length / BLOCK_SIZE`, the block loop, pStart, the height ternary, the entry
 loop with `column[p] += d`):
  T1 absent: column gives the block count, the height of the last block and the entries; d is added to each visited entry.
  T2 absent: blockCount bounds the loop and is read by the ternary; iBlock and p advance; pStart and height are read by the entry loop;
     no literal-initialised local; the ternary's two heights differ (the last block takes the rest of the column).
  T3 absent: both ends of each block are computed; the last block and the others are both handled; no rounding treatment remains in
     the text for anything ('No member handled'); no class is named in the gold's text.
  T4 absent: 'Adds a scalar to each entry of a column, block by block' is a general description that the loops address (like 'joins
     the elements'); 'block i starts at entry i * BLOCK_SIZE' is met; no phrase states a block size limit, a count rule or what happens
     to a short column; no inline comment; the identifiers (blockCount, pStart, height, p) name what they hold.

Single owner: only the gold decides which entries are visited; hops 1, 3 and 4 pass the array and the scalar along, and hop 2 only
returns early for an empty array. A caller cannot make the gold visit the entries of a short column without replacing it or handing
it another array and copying back. Declared alternatives (G9): hop 3 hands hop 4 a copy padded with BLOCK_SIZE - 1 extra entries (the
padded copy is updated, the column is not); hop 4 calls the gold twice; hop 2 also returns early when the value to add is zero. None
makes the trigger pass.
Recorded bypasses:
 B-0 the facade's original body, or a hop replacing its call by the loop `for (int i = 0; i < entries.length; i++) entries[i] += d;`,
     makes the gold (and the hops below) dead.
 B-1 a hop calls the gold on a padded copy and copies the entries back (several statements: copyOf, the call, System.arraycopy): a
     workaround around the gold's block count; the gold still leaves a short column unchanged against its own javadoc.

Lie: the facade's javadoc claims the entries are updated in two passes, first those at even indices and then those at odd indices; the
chain updates the entries in index order in a single pass. It names neither blocks, the block count nor any hop."""

ARV = "src/main/java/org/apache/commons/math/linear/ArrayRealVector.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
EDI = "src/main/java/org/apache/commons/math/linear/EigenDecompositionImpl.java"
BMI = "src/main/java/org/apache/commons/math/linear/BigMatrixImpl.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"

GOLD_TEXT = '''/**
 * Adds a scalar to each entry of a column, block by block.
 * <p>The entries are taken the way the rows of a block matrix are split:
 * block i starts at entry i * {@link #BLOCK_SIZE}.</p>
 * @param column the entries of the column, updated in place
 * @param d the scalar to add
 */
public static void addByBlocks(final double[] column, final double d) {
    final int blockCount = (column.length + BLOCK_SIZE - 1) / BLOCK_SIZE;
    for (int iBlock = 0; iBlock < blockCount; ++iBlock) {
        final int pStart = iBlock * BLOCK_SIZE;
        final int height = (iBlock == blockCount - 1) ? column.length - pStart : BLOCK_SIZE;
        for (int p = pStart; p < pStart + height; ++p) {
            column[p] += d;
        }
    }
}'''

HOP1 = '''/**
 * Add a scalar to each entry of a column given as an array.
 * @param column entries of the column, updated in place
 * @param d value to add to each entry
 */
public static void scalarAddToColumn(final double[] column, final double d) {
    MathUtils.addToAll(column, d);
}'''

HOP2 = '''/**
 * Adds a value to each element of an array, in place.
 * <p>An empty array is left as it is.</p>
 *
 * @param values the array to update
 * @param d the value to add
 */
public static void addToAll(double[] values, double d) {
    if (values.length == 0) {
        return;
    }
    EigenDecompositionImpl.addToEntries(values, d);
}'''

HOP3 = '''/**
 * Add a scalar to each entry of an array.
 * @param entries entries to update in place
 * @param d scalar to add
 */
public static void addToEntries(final double[] entries, final double d) {
    BigMatrixImpl.scalarAddEntries(entries, d);
}'''

HOP4 = '''/**
 * Adds a scalar to each entry of an array, in place.
 *
 * @param entries the entries to update
 * @param d the scalar to add
 */
public static void scalarAddEntries(double[] entries, double d) {
    BlockFieldMatrix.addByBlocks(entries, d);
}'''

DESIGN = {
 "instance": "Math-77", "project": "Math", "bug_id": 77, "seed": 3648,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the protected field data (double[], updated in place by the chain) and the scalar d, passed to hop 1; no field "
                 "is assigned, no write-back; the facade returns this",
 "host_mode": "1500", "host_lines": [1687, 1663, 1915, 1506, 1667],
 "reachability_probe": "mapAddToSelf first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-77-probe: ArrayRealVectorTest::testMapFunctions fails with PROBE-REACHED at "
                       "ArrayRealVector.mapAddToSelf(ArrayRealVector.java:347) via AbstractRealVector.mapAdd; full suite with the "
                       "probe: only testMapFunctions fails",
 "facade": {"file": ARV, "class": "org.apache.commons.math.linear.ArrayRealVector", "method": "mapAddToSelf", "near_line": 346},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/linear/ArrayRealVectorTest.java",
             "test_class": "org.apache.commons.math.linear.ArrayRealVectorTest", "test_method": "testMapFunctions"},
 "expected_signature": "compare vectors 0 elements differ expected:<3.0> but was:<1.0>",
 "gold": {"method": "addByBlocks", "text": GOLD_TEXT,
          "fault": {"old": "        final int blockCount = (column.length + BLOCK_SIZE - 1) / BLOCK_SIZE;",
                    "new": "        final int blockCount = column.length / BLOCK_SIZE;"}},
 "chain": {
   "facade_body": "BlockRealMatrix.scalarAddToColumn(data, d);\n        return this;",
   "lie": "The entries are updated in two passes, first those at even indices and then those at odd indices.",
   "hops": [
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "scalarAddToColumn",
      "imports": ["org.apache.commons.math.util.MathUtils"], "text": HOP1},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "addToAll",
      "imports": ["org.apache.commons.math.linear.EigenDecompositionImpl"], "text": HOP2},
     {"file": EDI, "class": "org.apache.commons.math.linear.EigenDecompositionImpl", "method": "addToEntries",
      "imports": [], "text": HOP3},
     {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "scalarAddEntries",
      "imports": [], "text": HOP4},
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "addByBlocks",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.linear.BlockFieldMatrix::createBlocksLayout",
              "org.apache.commons.math.linear.BlockRealMatrix::createBlocksLayout",
              "org.apache.commons.math.linear.OpenMapRealVector::mapAddToSelf"],
 "ownership_reason": "Only the gold decides which entries of the column are visited: it counts the blocks, computes the start and "
                     "height of each block and adds the scalar to each entry of each block. Hops 1, 3 and 4 pass the array and the "
                     "scalar along, and hop 2 only returns early for an empty array. With the block count rounded down, a column "
                     "shorter than one block has no block and keeps its entries, against the gold's javadoc ('Adds a scalar to each "
                     "entry of a column'); no caller can make the gold visit those entries without replacing it or handing it a "
                     "different array. The convention is pinned outside the gold: BlockFieldMatrix.createBlocksLayout and "
                     "BlockRealMatrix.createBlocksLayout count blocks as (rows + BLOCK_SIZE - 1) / BLOCK_SIZE, the last block "
                     "holding what remains (BlockFieldMatrix.blockHeight), with BlockFieldMatrixTest::testSeveralBlocks (37 x 41), "
                     "BlockFieldMatrixTest::testDimensions (smaller than one block) and BlockRealMatrixTest::testSeveralBlocks "
                     "passing; the step 'every entry receives d' is done by the intact OpenMapRealVector.mapAddToSelf and "
                     "ArrayRealVector.mapSubtractToSelf, with SparseRealVectorTest::testMapFunctions passing.",
 "ownership_tests": ["org.apache.commons.math.linear.BlockFieldMatrixTest::testSeveralBlocks",
                     "org.apache.commons.math.linear.BlockFieldMatrixTest::testDimensions",
                     "org.apache.commons.math.linear.BlockRealMatrixTest::testSeveralBlocks",
                     "org.apache.commons.math.linear.SparseRealVectorTest::testMapFunctions"],
 "compensating": {
   "chain": [
     {"file": EDI, "old": "    BigMatrixImpl.scalarAddEntries(entries, d);",
      "new": "    BigMatrixImpl.scalarAddEntries(Arrays.copyOf(entries, entries.length + BlockFieldMatrix.BLOCK_SIZE - 1), d);",
      "why": "hop 3 hands hop 4 a copy padded to whole blocks"},
     {"file": BMI, "old": "    BlockFieldMatrix.addByBlocks(entries, d);",
      "new": "    BlockFieldMatrix.addByBlocks(entries, d);\n        BlockFieldMatrix.addByBlocks(entries, d);",
      "why": "hop 4 calls the block routine twice"},
     {"file": MU, "old": "    if (values.length == 0) {",
      "new": "    if (values.length == 0 || d == 0) {",
      "why": "hop 2 also leaves the array as it is when the value to add is zero"},
   ],
 },
 "host_notes": "host_mode 1500: hosts drawn by `mr_lib.py preview Math-77 org/apache/commons/math/linear/ArrayRealVector.java 5` "
               "with the instance seed 3648, used in draw order, none substituted: linear.BlockRealMatrix (hop 1, 1687 lines, "
               "anchor after setRow, seed 3748), util.MathUtils (hop 2, 1663, after indicator, 3749), linear.EigenDecompositionImpl "
               "(hop 3, 1915, after getEigenvector, 3750), linear.BigMatrixImpl (hop 4, 1506, after equals, 3751; the smallest "
               "host), linear.BlockFieldMatrix (hop 5, gold, 1667, after setColumn, 3752). The facade's file ArrayRealVector is "
               "excluded by the draw. The pool has exactly five other public classes of at least 1500 lines, so the preview "
               "relaxed its package-distinctness heuristics (recorded by the preview). All five are public top-level classes in "
               "which a public static method compiles (BlockFieldMatrix is generic; the gold is a non-generic static method on "
               "double[] and uses the class constant BLOCK_SIZE = 36). The facade calls hop 1 by its simple name (same package); "
               "hop 1 imports util.MathUtils, hop 2 imports linear.EigenDecompositionImpl; hops 3 and 4 call same-package classes.",
}
