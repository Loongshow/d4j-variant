"""Main run Math-45__i (cell C10i, batch 9, sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Math-45; the real bug modified linear.OpenMapRealMatrix, the facade's class). No static pair (B8 note section 1: pool v2
found no tested public static method in OpenMapRealMatrix); no facade reuse (facade_planned_by null, facade_reuse_of null).

Facade: OpenMapRealMatrix.multiply(RealMatrix) (the single allowed candidate of batch9_tasks.json, "multiply", 23 lines,
CALLS_OWN_PUBLIC(1): the RealMatrix overload, which dispatches to the public overload multiply(OpenMapRealMatrix) and otherwise
computes the sparse-times-general product itself). The overload multiply(OpenMapRealMatrix) is not the candidate and stays intact
(it is the sibling pin below).
Original computation: if m is an OpenMapRealMatrix (the cast succeeds), the result of multiply(OpenMapRealMatrix); otherwise
(ClassCastException) the compatibility check MatrixUtils.checkMultiplicationCompatible(this, m), then a new BlockRealMatrix
(rows x m.getColumnDimension()) into which, for every stored entry of the private map entries (key = row * columns + column, value),
value * m.getEntry(k, j) is added at (row, j) for every column j of m (k = key % columns, row = key / columns).

facade_variant: V1 (state as parameters). state_passed: the private fields entries (OpenIntToDoubleHashMap, a public type of
math.util), rows and columns, together with the argument m, handed to hop 1; no field is written, no write-back. The facade keeps
the original guard: the dispatch to the sparse overload (try / cast / catch ClassCastException) and the compatibility check, then
makes one call to hop 1 and returns its result. The chain needs no method of the receiver (it reads the stored entries from the map
and the general matrix through RealMatrix), so V2 is not needed although the pool lists it as the candidate's best variant; the
facade calls no private method of its class (computeKey is not used; the chain decodes the key itself), so V4 does not apply; no
package-private type is involved (no V3/V5). No visibility is widened, no type is added, no signature, modifier, override or throws
clause changes, no reflection, no test edit.

Lie placement: the facade's javadoc is `/** {@inheritDoc} */` followed by `@Override`; the recipe's javadoc finder
(find_javadoc_start) only appends to a javadoc that is immediately adjacent to the header, and the annotation separates them, so the
recipe would not append the lie. The chain pre_edit therefore writes the javadoc as a block that keeps {@inheritDoc} and carries the
lie sentence (the same sentence as chain.lie, which the recipe then leaves unappended). Javadoc only; behaviour unchanged (G1).

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-45-probe of the fixture, the first statement of
multiply(RealMatrix) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.math.linear.SparseRealMatrixTest::testMultiply`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at OpenMapRealMatrix.multiply(OpenMapRealMatrix.java:150), called from
SparseRealMatrixTest.testMultiply(SparseRealMatrixTest.java:199). A second probe in the same copy put the throw at the start of the
catch block only ("PROBE-CATCH"); the FULL suite then has exactly one failing test, SparseRealMatrixTest::testMultiply (line 199,
m.multiply(new BlockRealMatrix(testDataInv))): no other test and no production caller reaches the general (non-sparse argument) path,
which is the path the chain carries. The facade is reached directly by the trigger.

Hosts (host_mode = "1500"; `mr_lib.py preview Math-45 org/apache/commons/math/linear/OpenMapRealMatrix.java 5`, seed 2150, the
seeded draw used in draw order, none substituted):
  hop 1 util.FastMath                      3791 lines  productOfEntries  plumbing: creates the BlockRealMatrix product (rows x the
                                                                         column count of m) and returns it
  hop 2 optimization.direct.BOBYQAOptimizer 2541 lines orderedProduct    placement: gathers the keys of the stored entries and sorts
                                                                         them into increasing (row-major) order
  hop 3 util.MathUtils                     2827 lines  keyedProduct      aggregation: looks up the value of each stored entry by key
  hop 4 dfp.Dfp                            2494 lines  sparseRows        pass-through
  hop 5 linear.BlockFieldMatrix            1549 lines  writeProductRows  GOLD: one pass over the stored entries in key order: decodes
                                                                         each key into its row and column, adds value times the matching
                                                                         row of m to the current row sums, and writes the sums as a row of
                                                                         the product once the last entry of that row has been read
The gold uses only RealMatrix (its host's own package) and arrays, so no import is added to BlockFieldMatrix; the locals of the gold
are plain (non-final) locals.
Host newline counts 3791, 2541, 2827, 2494, 1549; the smallest host (and the gold host) is BlockFieldMatrix (1549 lines).
The correct configuration returns the original product: every stored entry contributes value * m(k, j) to (row, j) exactly as in the
original; within a row the contributions are summed in increasing column order of the sparse matrix instead of the map's iteration
order (identical on every test input, all of which are exact in double arithmetic); rows without stored entries stay zero.

Fault (one-line omission of a state reset in the gold): after a finished row has been written, the row sums are not started afresh
(`sums = new double[width];`, which gives the next row a fresh array of zeros after setRow has copied the finished one, is dropped), so every later row of the product also carries the contributions of all earlier rows. The gold
then reads as an ordinary "sum per row, write at the end of the row" routine. Trigger: the EXISTING test
SparseRealMatrixTest::testMultiply; its second assertion, assertClose("inverse multiply", m.multiply(new BlockRealMatrix(testDataInv)),
identity, ...), fails with java.lang.AssertionError: inverse multiply (rows 1 and 2 of the product become (1, 1, 0) and (1, 1, 1)
instead of the identity rows). It is the only test that reaches the chain (catch-path probe above), and gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it writes the rows of the product of the sparse matrix and m; the stored entries come
in increasing key order; each row is written once the last entry of its row has been read) and is silent on clearing the sums. The
variant's rows are not the rows of the product on the trigger input. The convention (each row, indeed each entry, of a product is
summed from zero over its own terms only) is pinned outside the gold: the intact sibling overload OpenMapRealMatrix.multiply(
OpenMapRealMatrix) adds each product term only to the output entry of its own row (out.computeKey(i, j)), and
AbstractRealMatrix.multiply and BlockRealMatrix.multiply start every output sum at zero; passing tests: SparseRealMatrixTest::
testMultiply2, ::testPremultiply and ::testExamples (sparse products through the sibling overload) and BlockRealMatrixTest::testMultiply.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: keys bound the loop and give row and column; values scale the terms; columns decodes the keys; m supplies the terms and
     the width; out receives every row.
  T2 absent: e and j are advancing loop cursors; width bounds the inner loop and sizes sums (and its fresh array per row); row and inner are read by setRow, the
     row-end test and getEntry; sums is updated in the loop and written by setRow; the if decides whether a row is written.
  T3 absent: both halves of the key (row = key / columns, column = key % columns) are decoded and used; both ends of a row group (the
     end of the data, a change of row) end the row; no class named in the gold's text is handled in part.
  T4 absent: 'the rows of the product', 'in increasing order', 'row times the number of columns, plus its column' and 'written into
     out once the last stored entry of its row has been read' are met by lines of the body; 'rows without stored entries are left as
     they are' is met (setRow runs only for rows that have entries).
 Variant gold (javadoc, signature, the entry loop, the term loop, the row-end test with the single setRow):
  T1 absent: keys, values, columns, m and out each change the result or the side effect; none is only argument-checked.
  T2 absent: e and j advance; width, row, inner and sums are read by live statements (sums is updated by every entry and written by
     setRow); no local is initialised to a literal and frozen; the if has a live effect (it writes a row) and its two conditions are
     both live.
  T3 absent: the gold has no clearing or initialising step for the sums at all inside the loop ('No member handled'); row and column
     of the key are both decoded and used; both row-group ends are tested; the gold names no value class.
  T4 absent: 'the rows of the product' is a general description that the body addresses (sums of value times rows of m, written per
     row); 'in increasing order' (keys) is a caller precondition; the key layout and the write rule are met; 'left as they are' is met;
     no inline comment; identifiers (sums, row, inner, width, writeProductRows) name nothing the body does not meet.

Single owner: only the gold forms the row sums and writes the rows of the product; hop 1 only creates the zero product and returns it,
hop 2 only orders the keys, hop 3 only looks up the values, hop 4 passes everything through. Once the gold has written a row that still
carries earlier rows' contributions, no caller can separate them (the hops above the gold never read the product), so the rows can be
right only if the gold clears its sums or a caller replaces the gold. Declared alternatives (G9): hop 2 reads the keys in storage order
(no sort); hop 1 builds the product as an Array2DRowRealMatrix; hop 3 reads an absent key as zero explicitly. None makes the trigger
pass.
Recorded bypasses: B-0 the facade's original catch block (the per-entry addToEntry loop into a BlockRealMatrix) or the same loop in
hop 2 replacing the call to hop 3, discarding the rest of the chain including the gold; B-1 hop 4 calling the gold once per row with
that row's keys and values (a split of the gold's input by row, several lines, which re-implements the gold's row grouping).

Lie: the facade's javadoc claims that, when m is not sparse, its columns are first copied into dense arrays and each column of the
product is computed in turn as this matrix times one of them; no step of the chain copies the columns of m or works column by column
(the chain reads m entry by entry and builds the product row by row). It names neither the sums, their clearing, the rows nor any hop."""

OMR = "src/main/java/org/apache/commons/math/linear/OpenMapRealMatrix.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"
BOB = "src/main/java/org/apache/commons/math/optimization/direct/BOBYQAOptimizer.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"

LIE = ("When {@code m} is not sparse, its columns are first copied into dense arrays, and each column of the product is computed in "
       "turn as this matrix times one of them.")

GOLD_TEXT = '''/**
 * Writes the rows of the product of a sparse matrix and a matrix.
 *
 * <p>The sparse matrix is given by the keys of its stored entries, in
 * increasing order, and by their values; the key of an entry is its row
 * times the number of columns, plus its column. Each row of the product
 * is written into {@code out} once the last stored entry of its row has
 * been read; rows without stored entries are left as they are.</p>
 *
 * @param keys the keys of the stored entries, in increasing order
 * @param values the values of the stored entries
 * @param columns the number of columns of the sparse matrix
 * @param m the matrix to postmultiply by
 * @param out the matrix receiving the rows of the product
 */
public static void writeProductRows(final int[] keys, final double[] values, final int columns,
                                    final RealMatrix m, final RealMatrix out) {
    int width = m.getColumnDimension();
    double[] sums = new double[width];
    for (int e = 0; e < keys.length; e++) {
        int row = keys[e] / columns;
        int inner = keys[e] % columns;
        for (int j = 0; j < width; j++) {
            sums[j] += values[e] * m.getEntry(inner, j);
        }
        if (e + 1 == keys.length || keys[e + 1] / columns != row) {
            out.setRow(row, sums);
            sums = new double[width];
        }
    }
}'''

HOP1 = '''/**
 * Multiplies a sparse matrix, given by its stored entries, by a matrix.
 *
 * @param entries the stored entries of the sparse matrix, by key (the row
 * times the number of columns, plus the column)
 * @param rows the number of rows of the sparse matrix
 * @param columns the number of columns of the sparse matrix
 * @param m the matrix to postmultiply by
 * @return a new matrix holding the product
 */
public static RealMatrix productOfEntries(final OpenIntToDoubleHashMap entries,
                                          final int rows, final int columns,
                                          final RealMatrix m) {
    final RealMatrix out = new BlockRealMatrix(rows, m.getColumnDimension());
    BOBYQAOptimizer.orderedProduct(entries, columns, m, out);
    return out;
}'''

HOP2 = '''/**
 * Writes the product of a sparse matrix and a matrix into a matrix of
 * zeros, reading the stored entries of the sparse matrix in increasing
 * key order.
 *
 * @param entries the stored entries of the sparse matrix, by key
 * @param columns the number of columns of the sparse matrix
 * @param m the matrix to postmultiply by
 * @param out the matrix receiving the product
 */
public static void orderedProduct(final OpenIntToDoubleHashMap entries, final int columns,
                                  final RealMatrix m, final RealMatrix out) {
    final int[] keys = new int[entries.size()];
    int n = 0;
    for (OpenIntToDoubleHashMap.Iterator iterator = entries.iterator(); iterator.hasNext();) {
        iterator.advance();
        keys[n++] = iterator.key();
    }
    Arrays.sort(keys);
    MathUtils.keyedProduct(keys, entries, columns, m, out);
}'''

HOP3 = '''/**
 * Writes the product of a sparse matrix and a matrix into a matrix of
 * zeros, looking up the value of each stored entry by its key.
 *
 * @param keys the keys of the stored entries, in increasing order
 * @param entries the stored entries of the sparse matrix, by key
 * @param columns the number of columns of the sparse matrix
 * @param m the matrix to postmultiply by
 * @param out the matrix receiving the product
 */
public static void keyedProduct(final int[] keys, final OpenIntToDoubleHashMap entries, final int columns,
                                final RealMatrix m, final RealMatrix out) {
    final double[] values = new double[keys.length];
    for (int i = 0; i < keys.length; i++) {
        values[i] = entries.get(keys[i]);
    }
    Dfp.sparseRows(keys, values, columns, m, out);
}'''

HOP4 = '''/**
 * Writes the product of a sparse matrix and a matrix into a matrix of
 * zeros.
 *
 * @param keys the keys of the stored entries of the sparse matrix, in
 * increasing order
 * @param values the values of the stored entries
 * @param columns the number of columns of the sparse matrix
 * @param m the matrix to postmultiply by
 * @param out the matrix receiving the product
 */
public static void sparseRows(final int[] keys, final double[] values, final int columns,
                              final RealMatrix m, final RealMatrix out) {
    BlockFieldMatrix.writeProductRows(keys, values, columns, m, out);
}'''

FACADE_BODY = """try {
            return multiply((OpenMapRealMatrix) m);
        } catch (ClassCastException cce) {

            // safety check
            MatrixUtils.checkMultiplicationCompatible(this, m);

            return org.apache.commons.math.util.FastMath.productOfEntries(entries, rows, columns, m);
        }"""

JAVADOC_OLD = """    /** {@inheritDoc} */
    @Override
    public RealMatrix multiply(final RealMatrix m) {"""
JAVADOC_NEW = """    /**
     * {@inheritDoc}
     * When {@code m} is not sparse, its columns are first copied into
     * dense arrays, and each column of the product is computed in turn as
     * this matrix times one of them.
     */
    @Override
    public RealMatrix multiply(final RealMatrix m) {"""

DESIGN = {
 "instance": "Math-45", "project": "Math", "bug_id": 45, "seed": 2150,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private fields entries (OpenIntToDoubleHashMap), rows and columns, with the argument m, passed to hop 1 "
                 "inside the original catch block (dispatch to multiply(OpenMapRealMatrix) and the compatibility check kept); "
                 "no write-back",
 "host_mode": "1500", "host_lines": [3791, 2541, 2827, 2494, 1549],
 "reachability_probe": "multiply(RealMatrix) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-45-probe: SparseRealMatrixTest::testMultiply fails with PROBE-REACHED at "
                       "OpenMapRealMatrix.multiply(OpenMapRealMatrix.java:150) from SparseRealMatrixTest.java:199; a catch-block "
                       "probe makes only that test fail in the full suite",
 "facade": {"file": OMR, "class": "org.apache.commons.math.linear.OpenMapRealMatrix", "method": "multiply", "near_line": 149},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/linear/SparseRealMatrixTest.java",
             "test_class": "org.apache.commons.math.linear.SparseRealMatrixTest", "test_method": "testMultiply"},
 "expected_signature": "AssertionFailedError: inverse multiply",
 "gold": {"method": "writeProductRows", "text": GOLD_TEXT,
          "fault": {"old": "            if (e + 1 == keys.length || keys[e + 1] / columns != row) {\n"
                           "                out.setRow(row, sums);\n"
                           "                sums = new double[width];\n"
                           "            }",
                    "new": "            if (e + 1 == keys.length || keys[e + 1] / columns != row) {\n"
                           "                out.setRow(row, sums);\n"
                           "            }"}},
 "pre_edits": {"chain": [{"file": OMR, "old": JAVADOC_OLD, "new": JAVADOC_NEW}]},
 "chain": {
   "facade_body": FACADE_BODY,
   "lie": LIE,
   "hops": [
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "productOfEntries",
      "imports": ["org.apache.commons.math.linear.BlockRealMatrix", "org.apache.commons.math.linear.RealMatrix",
                  "org.apache.commons.math.optimization.direct.BOBYQAOptimizer"], "text": HOP1},
     {"file": BOB, "class": "org.apache.commons.math.optimization.direct.BOBYQAOptimizer", "method": "orderedProduct",
      "imports": ["java.util.Arrays", "org.apache.commons.math.linear.RealMatrix", "org.apache.commons.math.util.MathUtils",
                  "org.apache.commons.math.util.OpenIntToDoubleHashMap"], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "keyedProduct",
      "imports": ["org.apache.commons.math.dfp.Dfp", "org.apache.commons.math.linear.RealMatrix"], "text": HOP3},
     {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "sparseRows",
      "imports": ["org.apache.commons.math.linear.BlockFieldMatrix", "org.apache.commons.math.linear.RealMatrix"], "text": HOP4},
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "writeProductRows",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.linear.OpenMapRealMatrix::multiply",
              "org.apache.commons.math.linear.AbstractRealMatrix::multiply",
              "org.apache.commons.math.linear.BlockRealMatrix::multiply"],
 "ownership_reason": "Only the gold forms the row sums of the product and writes the rows: it reads the stored entries of the "
                     "sparse matrix in increasing key order, adds value times the matching row of m to the sums of the current row "
                     "and writes the sums as a row of the product once the last entry of that row has been read. Hop 1 only creates "
                     "the zero product and returns it, hop 2 only orders the keys, hop 3 only looks up the values and hop 4 passes "
                     "everything through; none of them reads the product, so once the gold has written a row that still carries "
                     "earlier rows' contributions no caller can separate them. The gold's javadoc promises the rows of the product; "
                     "on the trigger the variant's rows 1 and 2 carry row 0's (and row 1's) terms. The convention that each row of a "
                     "product is summed from zero over its own terms only is pinned outside the gold: the intact sibling overload "
                     "OpenMapRealMatrix.multiply(OpenMapRealMatrix) adds every term only to the entry of its own row "
                     "(out.computeKey(i, j)), and AbstractRealMatrix.multiply and BlockRealMatrix.multiply start each output sum at "
                     "zero; SparseRealMatrixTest::testMultiply2, ::testPremultiply and ::testExamples (sparse products through the "
                     "sibling overload) and BlockRealMatrixTest::testMultiply pass.",
 "ownership_tests": ["org.apache.commons.math.linear.SparseRealMatrixTest::testMultiply2",
                     "org.apache.commons.math.linear.SparseRealMatrixTest::testPremultiply",
                     "org.apache.commons.math.linear.SparseRealMatrixTest::testExamples",
                     "org.apache.commons.math.linear.BlockRealMatrixTest::testMultiply"],
 "compensating": {
   "chain": [
     {"file": BOB, "old": "Arrays.sort(keys);\n        MathUtils.keyedProduct(keys, entries, columns, m, out);",
      "new": "MathUtils.keyedProduct(keys, entries, columns, m, out);",
      "why": "hop 2 reads the keys in storage order"},
     {"file": FM, "old": "final RealMatrix out = new BlockRealMatrix(rows, m.getColumnDimension());",
      "new": "final RealMatrix out = new org.apache.commons.math.linear.Array2DRowRealMatrix(rows, m.getColumnDimension());",
      "why": "hop 1 builds the product as an array matrix"},
     {"file": MU, "old": "values[i] = entries.get(keys[i]);",
      "new": "values[i] = entries.containsKey(keys[i]) ? entries.get(keys[i]) : 0.0;",
      "why": "hop 3 reads an absent key as zero"},
   ],
 },
 "host_notes": "host_mode 1500: hosts from the recipe's seeded draw `mr_lib.py preview Math-45 "
               "org/apache/commons/math/linear/OpenMapRealMatrix.java 5` (seed 2150; the facade file excluded; FastMathLiteralArrays "
               "is unusable in the pool), used in draw order, none substituted: util.FastMath (hop 1, 3791 lines), "
               "optimization.direct.BOBYQAOptimizer (hop 2, 2541), util.MathUtils (hop 3, 2827), dfp.Dfp (hop 4, 2494), "
               "linear.BlockFieldMatrix (hop 5, gold, 1549; the smallest host; the draw note says the package-distinctness "
               "heuristic was relaxed for hops 5-6 because the pool is small). All five are public top-level classes in which a "
               "public static method compiles (BlockFieldMatrix is generic; the gold is a non-generic static method using "
               "RealMatrix of its own package). Anchors from the recipe with seed 2150 + 100 + i: hop 1 after abs (2250), hop 2 "
               "after the BOBYQAOptimizer constructor (2251), hop 3 after equalsIncludingNaN (2252), hop 4 after ceil (2253), hop 5 "
               "after multiply (2254). The facade calls hop 1 by its fully qualified name; each hop imports the next host and the "
               "types it needs. The facade's {@inheritDoc} javadoc is separated from the header by @Override, so the lie is "
               "written by a javadoc-only chain pre_edit (see the docstring).",
}
