"""Main run Math-98__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade; fixed
checkout of Defects4J Math-98, whose real bug modified BigMatrixImpl and RealMatrixImpl). No static pair (B8 note section 1).

Facade: BigMatrixImpl.getSubMatrix(int[] selectedRows, int[] selectedColumns) (the third allowed candidate of batch8_tasks.json, 21
lines, facade_planned_by null; BATCH8_PREREGISTRATION.md row 303; no facade reuse). The two range overloads
(BigMatrixImpl.getSubMatrix(int, int, int, int) and RealMatrixImpl.getSubMatrix(int, int, int, int)) were not used: their whole
decision logic is the argument guard on the four range ends, which stays in the facade, and the remaining computation is one
System.arraycopy per row, with no iteration or decision in which a one-line omission leaves no unused parameter or frozen cursor.
Original computation: an empty row or column selection gives MatrixIndexException (the guard); otherwise a new
BigDecimal[selectedRows.length][selectedColumns.length] receives, at (i, j), the entry data[selectedRows[i]][selectedColumns[j]]
(the same BigDecimal instance); an index outside the matrix raises ArrayIndexOutOfBoundsException, which is turned into
MatrixIndexException("matrix dimension mismatch"); the array becomes the data of a new BigMatrixImpl(subMatrixData, false).

facade_variant: V1 (state as parameters). state_passed: the protected field data (BigDecimal[][], read inside BigMatrixImpl) and the
two selection arrays are handed to hop 1; no field is written, no write-back. The facade body is the original guard (the emptiness
check, text unchanged) plus one call to hop 1 by its fully-qualified name. The computation calls no private method of BigMatrixImpl
(no V4), needs no method of the receiver (no V2) and no package-private type (BigDecimal, BigMatrix, BigMatrixImpl and
MatrixIndexException are public; no V3/V5). No visibility is widened, no type is added, no signature, modifier, override or throws
clause changes, no reflection, no test edit.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-98-probe/w of the fixture, the first statement
of getSubMatrix(int[], int[]) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.math.linear.BigMatrixImplTest::testSubMatrix`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at BigMatrixImpl.getSubMatrix(BigMatrixImpl.java:611), called from BigMatrixImplTest.testSubMatrix
(BigMatrixImplTest.java:571). Full suite with the probe: 1 failing test (BigMatrixImplTest::testSubMatrix only; the method has no
production caller and no other test calls it). The facade is reached directly by the trigger.

Hosts (host_mode = "largest5"; hosts_hop_order of batch8_tasks.json, in that order, none substituted; the allowed candidates' files
BigMatrixImpl.java and RealMatrixImpl.java are excluded):
  hop 1 stat.inference.TTestImpl            1059 lines  subMatrixOf    aggregation: wraps the selected entries into a new BigMatrixImpl
                                                                       without copying them
  hop 2 geometry.Rotation                   1057 lines  selectEntries  decision: rejects an index that is not a row or a column of the
                                                                       matrix (MatrixIndexException "matrix dimension mismatch", the
                                                                       original's message) before any entry is read
  hop 3 util.MathUtils                      1041 lines  entriesAt      placement: lays the rows of the matrix out one after the other in
                                                                       one array (row-major) and passes it on with the row width
  hop 4 ode.GraggBulirschStoerIntegrator    1020 lines  copyEntries    pass-through
  hop 5 complex.Complex                      877 lines  gatherEntries  GOLD: allocates the result and walks each selected row of the
                                                                       row-major array, the read position moving from one selected
                                                                       column to the next (by the difference of the column indices),
                                                                       storing the entry met at each step; after a row the walk's
                                                                       column returns to 0 for the next row
Host newline counts 1059, 1057, 1041, 1020, 877; the smallest host (and the gold host) is Complex with 877 lines (C10F addendum
section 1: hosts under 1500 lines are expected in this regime).
The correct configuration returns the original result for every input: valid selections give the same BigDecimal instances at the
same positions (position = rows[i] * width + columns[j] for every j, because the walk starts each row at its first entry with its
column at 0); an index outside the matrix (negative, a row at or past the row count, a column at or past the column count) gives
MatrixIndexException("matrix dimension mismatch") as the original does, here before any entry is read; the original guard is kept
verbatim.

Fault (one-line omission of a special-case step in the gold, a state reset): the end-of-row reset `column = 0;` of the walk is
dropped. The walk of every row after the first then starts from the column at which the previous row ended, so its read positions
are moved back by that column. Trigger: the EXISTING test BigMatrixImplTest::testSubMatrix; its three range-overload assertions pass
(untouched overload), and the first index-array assertion, getSubMatrix({0, 2}, {1, 3}) on the 4 x 4 matrix
{{1, 2, 3, 4}, {1.5, 2.5, 3.5, 4.5}, {2, 4, 6, 8}, {4, 5, 6, 7}}, returns {{2, 4}, {3.5, 2}} instead of {{2, 4}, {4, 8}} (row 2 is
read at columns -2 and 0 relative to its start, i.e. row 1 column 2 and row 2 column 0), so the test fails with
junit.framework.AssertionFailedError: Rows02Cols13 expected:<...> but was:<...>. It is the only test that newly fails: the facade has
no production caller and no other test calls it (probe above), and the new hops have no other caller; gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (entry (i, j) of the result is the entry of the matrix in row rows[i] and column
columns[j]) and is silent on the walk's per-row return to column 0; on the trigger input entry (1, 0) of the result is the entry of row
1, column 2 (3.5), not that of row 2, column 1 (4), which violates the contract on a valid selection. The convention is pinned outside
the gold: the intact sibling RealMatrixImpl.getSubMatrix(int[], int[]) reads every selected row at the selected columns
independently (subI[j] = dataSelectedI[selectedColumns[j]]), BigMatrixImpl.getEntry and BigMatrixImpl.getRowMatrix read row r,
column c at data[r][c]; passing tests RealMatrixImplTest::testSubMatrix (the same {0, 2} / {1, 3} and {3, 1} / {3, 1} selections on
the double sibling), BigMatrixImplTest::testGetRowMatrix and BigMatrixImplTest::testGetColumnMatrix (same data).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (with the end-of-row `column = 0;`):
  T1 absent: entries supplies every stored value; width is the row stride of position; rows gives each row start and the result
     height; columns gives every step and the result width; none is only argument-checked (the gold has no argument check).
  T2 absent: gathered is returned; line is written; position is set per row and advanced in the inner loop; column is assigned in
     the inner loop and at the end of each row, read by every step; i and j advance; the initial 0 of column is read by the first
     step of row 0 (no dead store); there is no branch, case or ternary.
  T3 absent: row and column indices both enter every read position; no enum, type code or named format; no range ends; the gold's
     text names no class it handles in part.
  T4 absent: 'Entry (i, j) of the result is the entry of the matrix in row rows[i] and column columns[j]' and 'stored row by row in
     one array' are general descriptions the walk addresses; '@return a new array of rows.length rows of columns.length entries' is
     met by the allocation; the @param clauses are caller descriptions; no @throws clause, no inline comment.
 Variant gold (javadoc, signature, gathered allocation, int column = 0, the two loops, line = gathered[i], int position =
 rows[i] * width, position += columns[j] - column, column = columns[j], line[j] = entries[position], return gathered):
  T1 absent: entries (read at every step), width (row stride in position), rows (row start, result height) and columns (every step,
     result width) each change the result.
  T2 absent: gathered is returned; line is written; position is set per row and advanced inside the inner loop; column is
     initialised to 0 and reassigned inside the loop (column = columns[j]), and read at every step, so it is neither dead nor frozen;
     i and j are advanced by their loops; there is no decision of any kind.
  T3 absent: no enumeration and no closed set with a member left out: row and column both enter the position; there is no reset of
     any kind in the walk ('No member handled', as the checklist's 'a word loop with no reset'); no range ends; no class named in the
     gold's text (none of 'valid', 'within', 'bounds', 'finite') is handled in part.
  T4 absent: 'Gathers entries of a matrix whose entries are stored row by row in one array' and 'Entry (i, j) of the result is the
     entry of the matrix in row rows[i] and column columns[j]' are general descriptions that the body addresses (row start rows[i] *
     width, steps over columns[j]); '@param width the number of columns of the matrix' is a caller description and width is used as
     the row stride; '@return a new array of rows.length rows of columns.length entries' is met by the allocation; no @throws
     clause, no inline comment; the identifiers (gathered, line, position, column, entries, width) name what they hold.

Single owner: only the gold reads entries of the matrix at the selected positions: hop 2 checks the indices and reads no entry, hop 3
copies the whole matrix row by row (the selections pass through it unread), hops 1 and 4 pass along. The misplaced reads depend on the
row (only rows after the first) and on the last selected column, so no one-line change at a hop can undo them: a different layout,
stride or index check at hops 2-3 moves every row alike, and once the gold has stored row 1, column 2 at (1, 0), no caller can tell
it apart from a valid entry (3.5 is an ordinary value). Declared alternatives (G9): hop 1 builds the matrix with the copying
constructor; hop 3 takes the width from the last row; hop 4 hands a copy of the column selection on. None makes the trigger pass.
Recorded bypasses (not one-line, and they make the gold's walk dead or split it):
 B-0 the facade's original body, or a hop reading data[rows[i]][columns[j]] directly, re-implements the whole gather and makes the
     chain below it, including the gold, dead.
 B-1 a hop calling the gold once per selected row (one-row selections) and assembling the rows: several statements, a second
     driver of the gold's row loop, against the hops' documented single hand-on of the whole selection.

Lie: the facade's javadoc claims the entries are copied column by column, each selected column being read in one pass over the
selected rows; the chain lays the matrix out row by row and the gold walks the selection row by row (outer loop over the rows). It
names neither the walk's state, nor its reset, nor any hop."""

BMI = "src/java/org/apache/commons/math/linear/BigMatrixImpl.java"
TTI = "src/java/org/apache/commons/math/stat/inference/TTestImpl.java"
ROT = "src/java/org/apache/commons/math/geometry/Rotation.java"
MU = "src/java/org/apache/commons/math/util/MathUtils.java"
GBS = "src/java/org/apache/commons/math/ode/GraggBulirschStoerIntegrator.java"
CPX = "src/java/org/apache/commons/math/complex/Complex.java"

GOLD_TEXT = '''/**
 * Gathers entries of a matrix whose entries are stored row by row in one
 * array.
 * <p>
 * Entry (i, j) of the result is the entry of the matrix in row rows[i]
 * and column columns[j].</p>
 *
 * @param entries the entries of the matrix, row by row
 * @param width the number of columns of the matrix
 * @param rows the indices of the rows to gather
 * @param columns the indices of the columns to gather
 * @return a new array of rows.length rows of columns.length entries
 */
public static BigDecimal[][] gatherEntries(BigDecimal[] entries, int width,
    int[] rows, int[] columns) {
    final BigDecimal[][] gathered = new BigDecimal[rows.length][columns.length];
    int column = 0;
    for (int i = 0; i < rows.length; i++) {
        final BigDecimal[] line = gathered[i];
        int position = rows[i] * width;
        for (int j = 0; j < columns.length; j++) {
            position += columns[j] - column;
            column = columns[j];
            line[j] = entries[position];
        }
        column = 0;
    }
    return gathered;
}'''

HOP1 = '''/**
 * Gets the submatrix of a matrix at the selected rows and columns.
 * <p>
 * The selected entries are wrapped into the new matrix as they are,
 * without being copied again.</p>
 *
 * @param data the entries of the matrix, row by row
 * @param rows the indices of the selected rows
 * @param columns the indices of the selected columns
 * @return the submatrix, with one row per selected row and one column
 * per selected column
 */
public static BigMatrix subMatrixOf(BigDecimal[][] data, int[] rows, int[] columns) {
    return new BigMatrixImpl(Rotation.selectEntries(data, rows, columns), false);
}'''

HOP2 = '''/** Select the entries of a matrix at given rows and columns.
 * <p>Every index is checked against the dimensions of the matrix before
 * any entry is read.</p>
 * @param data entries of the matrix, row by row
 * @param rows indices of the selected rows
 * @param columns indices of the selected columns
 * @return selected entries, one row per selected row
 * @exception MatrixIndexException if an index is not a row or a column
 * of the matrix
 */
public static BigDecimal[][] selectEntries(BigDecimal[][] data, int[] rows, int[] columns)
    throws MatrixIndexException {
    for (int i = 0; i < rows.length; i++) {
        if (rows[i] < 0 || rows[i] >= data.length) {
            throw new MatrixIndexException("matrix dimension mismatch");
        }
    }
    for (int j = 0; j < columns.length; j++) {
        if (columns[j] < 0 || columns[j] >= data[0].length) {
            throw new MatrixIndexException("matrix dimension mismatch");
        }
    }
    return MathUtils.entriesAt(data, rows, columns);
}'''

HOP3 = '''/**
 * Returns entries of a matrix at the given rows and columns.
 * <p>
 * The rows of the matrix are first laid out one after the other in a
 * single array, which is passed on with the row width.</p>
 *
 * @param data the entries of the matrix, row by row
 * @param rows the indices of the rows
 * @param columns the indices of the columns
 * @return the entries, one row per index in rows and one column per index
 *         in columns
 */
public static BigDecimal[][] entriesAt(BigDecimal[][] data, int[] rows, int[] columns) {
    final int width = data[0].length;
    final BigDecimal[] entries = new BigDecimal[data.length * width];
    for (int r = 0; r < data.length; r++) {
        System.arraycopy(data[r], 0, entries, r * width, width);
    }
    return GraggBulirschStoerIntegrator.copyEntries(entries, width, rows, columns);
}'''

HOP4 = '''/** Copy entries of a matrix stored row by row in one array.
 * @param entries entries of the matrix, row by row
 * @param width number of columns of the matrix
 * @param rows indices of the rows to copy
 * @param columns indices of the columns to copy
 * @return copied entries, one row per index in rows and one column per
 * index in columns
 */
public static java.math.BigDecimal[][] copyEntries(java.math.BigDecimal[] entries, int width,
                                                   int[] rows, int[] columns) {
    return org.apache.commons.math.complex.Complex.gatherEntries(entries, width, rows, columns);
}'''

DESIGN = {
 "instance": "Math-98", "project": "Math", "bug_id": 98, "seed": 7994,
 "src_root": "src/java", "test_root": "src/test",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the protected field data (BigDecimal[][]) and the two selection arrays selectedRows and selectedColumns, passed to "
                 "hop 1; no field is written, no write-back",
 "host_mode": "largest5", "host_lines": [1059, 1057, 1041, 1020, 877],
 "reachability_probe": "getSubMatrix(int[], int[]) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-98-probe/w: BigMatrixImplTest::testSubMatrix fails with PROBE-REACHED at "
                       "BigMatrixImpl.getSubMatrix(BigMatrixImpl.java:611) from BigMatrixImplTest.java:571; full suite with the "
                       "probe: 1 failing test (BigMatrixImplTest::testSubMatrix)",
 "facade": {"file": BMI, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "getSubMatrix", "near_line": 609},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/math/linear/BigMatrixImplTest.java",
             "test_class": "org.apache.commons.math.linear.BigMatrixImplTest", "test_method": "testSubMatrix"},
 "expected_signature": "Rows02Cols13",
 "gold": {"method": "gatherEntries", "text": GOLD_TEXT,
          "fault": {"old": "                line[j] = entries[position];\n"
                           "            }\n"
                           "            column = 0;\n"
                           "        }\n",
                    "new": "                line[j] = entries[position];\n"
                           "            }\n"
                           "        }\n"}},
 "chain": {
   "facade_body": "if (selectedRows.length * selectedColumns.length == 0) {\n"
                  "            throw new MatrixIndexException(\n"
                  "            \"selected row and column index arrays must be non-empty\");\n"
                  "        }\n"
                  "        return org.apache.commons.math.stat.inference.TTestImpl.subMatrixOf(data, selectedRows, selectedColumns);",
   "lie": "The entries are copied column by column, each selected column being read in one pass over the selected rows.",
   "hops": [
     {"file": TTI, "class": "org.apache.commons.math.stat.inference.TTestImpl", "method": "subMatrixOf",
      "imports": ["java.math.BigDecimal", "org.apache.commons.math.geometry.Rotation",
                  "org.apache.commons.math.linear.BigMatrix", "org.apache.commons.math.linear.BigMatrixImpl"], "text": HOP1},
     {"file": ROT, "class": "org.apache.commons.math.geometry.Rotation", "method": "selectEntries",
      "imports": ["java.math.BigDecimal", "org.apache.commons.math.linear.MatrixIndexException",
                  "org.apache.commons.math.util.MathUtils"], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "entriesAt",
      "imports": ["org.apache.commons.math.ode.GraggBulirschStoerIntegrator"], "text": HOP3},
     {"file": GBS, "class": "org.apache.commons.math.ode.GraggBulirschStoerIntegrator", "method": "copyEntries",
      "imports": [], "text": HOP4},
     {"file": CPX, "class": "org.apache.commons.math.complex.Complex", "method": "gatherEntries",
      "imports": ["java.math.BigDecimal"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.linear.RealMatrixImpl::getSubMatrix",
              "org.apache.commons.math.linear.BigMatrixImpl::getEntry",
              "org.apache.commons.math.linear.BigMatrixImpl::getRowMatrix"],
 "ownership_reason": "Only the gold reads entries of the matrix at the selected positions: hop 2 checks the indices against the "
                     "dimensions and reads no entry, hop 3 lays the whole matrix out row by row in one array and passes the "
                     "selections on unread, hops 1 and 4 pass along. The gold's javadoc promises that entry (i, j) of the result is "
                     "the entry of the matrix in row rows[i] and column columns[j]; for the valid selection {0, 2} / {1, 3} of the "
                     "4 x 4 test matrix the variant stores at (1, 0) the entry of row 1, column 2 (3.5) instead of that of row 2, "
                     "column 1 (4), and at (1, 1) the entry of row 2, column 0 (2) instead of row 2, column 3 (8): the rows after "
                     "the first are read from the column where the previous row ended. The misplacement depends on the row and on "
                     "the last selected column, so no layout, stride or check at a hop undoes it, and a stored entry is an ordinary "
                     "value no caller can tell apart from the right one. The convention that each selected row is read at the "
                     "selected columns independently is pinned outside the gold: the intact sibling "
                     "RealMatrixImpl.getSubMatrix(int[], int[]) (subI[j] = dataSelectedI[selectedColumns[j]] for every selected "
                     "row), BigMatrixImpl.getEntry and BigMatrixImpl.getRowMatrix (row r, column c at data[r][c]); "
                     "RealMatrixImplTest::testSubMatrix (the same selections on the double sibling), "
                     "BigMatrixImplTest::testGetRowMatrix and BigMatrixImplTest::testGetColumnMatrix pass.",
 "ownership_tests": ["org.apache.commons.math.linear.RealMatrixImplTest::testSubMatrix",
                     "org.apache.commons.math.linear.BigMatrixImplTest::testGetRowMatrix",
                     "org.apache.commons.math.linear.BigMatrixImplTest::testGetColumnMatrix"],
 "compensating": {
   "chain": [
     {"file": TTI, "old": "return new BigMatrixImpl(Rotation.selectEntries(data, rows, columns), false);",
      "new": "return new BigMatrixImpl(Rotation.selectEntries(data, rows, columns));",
      "why": "hop 1 builds the matrix with the copying constructor"},
     {"file": MU, "old": "final int width = data[0].length;",
      "new": "final int width = data[data.length - 1].length;",
      "why": "hop 3 takes the row width from the last row"},
     {"file": GBS, "old": "return org.apache.commons.math.complex.Complex.gatherEntries(entries, width, rows, columns);",
      "new": "return org.apache.commons.math.complex.Complex.gatherEntries(entries, width, rows, (int[]) columns.clone());",
      "why": "hop 4 hands a copy of the column selection on"},
   ],
 },
 "host_notes": "host_mode largest5: hosts are hosts_hop_order of batch8_tasks.json (the five largest public, non-interface, non-enum "
               "classes on the checkout other than the allowed candidates' files BigMatrixImpl.java and RealMatrixImpl.java), in "
               "that order, none substituted, none chosen by this builder: stat.inference.TTestImpl (hop 1, 1059 lines), "
               "geometry.Rotation (hop 2, 1057), util.MathUtils (hop 3, 1041; final class with a private constructor, which does not "
               "affect a static method), ode.GraggBulirschStoerIntegrator (hop 4, 1020), complex.Complex (hop 5, gold, 877; the "
               "smallest host). All five are public top-level classes in which a public static method compiles. Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 7994 + 100 + i, as mr3_spec.py inserts them (recorded in the spec's "
               "stage_b.hops). The facade calls hop 1 by its fully-qualified name; each hop imports the next host and "
               "java.math.BigDecimal as needed, except hop 4: GraggBulirschStoerIntegrator.java has no import statement, so hop 4 "
               "names java.math.BigDecimal and complex.Complex by their fully-qualified names; hop 1 imports linear.BigMatrix and "
               "linear.BigMatrixImpl; hop 2 imports linear.MatrixIndexException; the gold imports only java.math.BigDecimal.",
}
