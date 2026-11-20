"""Main run Chart-22__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Chart-22, revision 227; the real bug modified org.jfree.data.KeyedObjects2D, the facade's class). Batch 8: the bug has no
static-facade instance (pool v2: no_tested_static), so there is no paired instance (B8 note section 1).

Facade: KeyedObjects2D.setObject(Object, Comparable, Comparable) (allowed instance target of BATCH8_PREREGISTRATION.md row 217,
facade_planned_by = null; no facade reuse). The other two allowed targets were not used: both getObject overloads are pure lookups
whose only behaviour that a single existing test observes is the unknown-key / invalid-index exception path (the found and the
missing-in-row paths are asserted identically by testGetValueByKey and testSetObject, and by ~27 tests for getObject(int, int)),
and a missing key or index check is a decision that any hop above the gold can pre-filter with one added line, which the fault
rule excludes.
Original computation of the facade: null checks on rowKey and columnKey (IllegalArgumentException); the row with the given key is
looked up in rowKeys (rows.get(rowIndex)) or, when the key is absent, the key is appended to rowKeys and a new KeyedObjects row is
appended to rows; the object is stored in that row under the column key (KeyedObjects.setObject replaces an existing entry or
appends a new one); the column key is appended to columnKeys only when it is not already there.

facade_variant: V1 (state as parameters). The method reads three private fields (rowKeys, columnKeys, rows: java.util.List
values that it mutates but never reassigns; no field is written): the facade keeps the original argument guard (the two null
checks), reads the three private fields (inside KeyedObjects2D, so no visibility change) and passes them, with object, rowKey and
columnKey, to hop 1. The chain mutates the same List objects exactly as the original body did, so there is no write-back. The
chain needs no method of the receiver (V2 not needed), no private method of KeyedObjects2D (no V4), and the only data type it
names, org.jfree.data.KeyedObjects, is a public class (no V3/V5). No signature, modifier, override or throws change; no new type;
no reflection; no test edit.
state_passed: the private fields rowKeys, columnKeys and rows (the List objects themselves) to hop 1, with the parameters object,
rowKey and columnKey; no write-back (the chain appends to the passed lists, as the original body did).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Chart-22-pset of the fixture, the
first statement of setObject was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. Full suite: 35 failing
tests, all with java.lang.IllegalStateException: PROBE-REACHED, among them KeyedObjects2DTests::testRemoveValue (the trigger),
testSetObject, testGetValueByKey, testCloning, and the DefaultBoxAndWhiskerCategoryDataset / DefaultStatisticalCategoryDataset /
box-and-whisker and statistical renderer tests (addObject, removeObject and the two datasets' add methods call setObject). The
same probe on getObject(Comparable, Comparable) gave 5 failing tests and on getObject(int, int) 27; the unprobed fixture gives 0.
The facade is reached by existing tests directly.

Hosts (host_mode = "1500"; `mr_lib.py preview Chart-22 org/jfree/data/KeyedObjects2D.java 5` with the instance seed 2296, the
draw excluding the facade file; used in draw order, nothing substituted):
  hop 1 org.jfree.chart.ChartPanel                                    2502 lines  addOrUpdateObject  pass-through
  hop 2 org.jfree.chart.plot.SpiderWebPlot                            1654 lines  setObjectInTable   pass-through
  hop 3 org.jfree.chart.plot.ThermometerPlot                          1537 lines  storeByRowKey      placement step: the row with
                                                                                                     the given key, or a new row
                                                                                                     appended to the table
  hop 4 org.jfree.chart.renderer.category.AbstractCategoryItemRenderer 1702 lines setRowObject       pass-through
  hop 5 org.jfree.chart.renderer.xy.AbstractXYItemRenderer            1750 lines  putObjectInRow     GOLD: stores the object in the
                                                                                                     row and makes the column key a
                                                                                                     column of the table
Host newline counts 2502, 1654, 1537, 1702, 1750; the smallest host is ThermometerPlot (1537 lines); the gold host has 1750 lines.
The correct configuration performs the original body's steps in the original order on the same List objects, so it is
behaviour-identical to the original setObject for every input.

Fault (one-line omission of a decision in the gold): the test that the column key is not yet among the column keys is dropped,
so every call appends the column key, and an update of an object in an existing column records that column a second time. The
gold then reads as the ordinary routine "store the object in the row; record the column key". Trigger: the EXISTING test
KeyedObjects2DTests::testRemoveValue: setObject("Obj1", "R1", "C1"), setObject("Obj2", "R2", "C2"), then removeObject("R2", "C2"),
whose first step is setObject(null, "R2", "C2") (an update of the existing column C2, which the variant records twice); removeObject
then removes the emptied row and removes the emptied column key once, so assertEquals(1, data.getColumnCount()) fails with
expected:<1> but was:<2>. It is the only test that newly fails in the full suite (checked on a scratch copy with the same omission
in place: 1 failing test, testRemoveValue): every other test that updates an existing column never counts or compares the column
keys afterwards in a way the duplicate changes.

The gold's javadoc states the idiomatic contract (the object is stored in the row under the column key, replacing an object already
stored there, and the column key is made one of the columns of the table) and is silent on the containment test; an update that
gives the table a second column for the same key does not make the key "one of the columns", it adds a phantom column
(getColumnCount() counts it). The convention is pinned outside the gold: DefaultKeyedValues2D.setValue, the sibling table of
Numbers, does the same step (`int columnIndex = this.columnKeys.indexOf(columnKey); if (columnIndex < 0) { this.columnKeys.add(...)
}`), with DefaultKeyedValues2DTests::testRemoveValueBug1690654 (the same add / add / remove sequence on DefaultKeyedValues2D:
getColumnCount() 2 then 1) and ::testColumnCount passing; KeyedObjects.setObject (the row the gold writes into) replaces the object
under an existing key instead of appending a second entry (KeyedObjectsTests::testSetObject); KeyedObjects2D.getColumnCount is
columnKeys.size() ("Returns the column count"). The facade's own javadoc ("Adds or updates an object.") is kept and the lie appended.

Single owner: only the gold records column keys; hops 1, 2 and 4 pass their arguments along unchanged and hop 3 only chooses the
row (it never touches columnKeys). No one-line edit above the gold restores the contract while keeping every method used as
documented: a hop cannot keep the gold from appending without either not calling it (then the object is not stored, or the hop
stores it itself: a bypass) or handing it another list (the column-key output of the gold becomes dead: a bypass); removing the key
from columnKeys before the call moves the column to the end of the table on every update, against the hops' javadoc ("An update
leaves the existing rows and columns where they are"), KeyedObjects.setObject's in-place replacement and DefaultKeyedValues2D.setValue.
(Checked on the variant in a scratch copy: `columnKeys.remove(columnKey);` before the call in hop 4 passes the trigger and the full
suite, since no test reads the column order after an update; it is excluded by that documentation, not by a test.)
Declared alternatives (G9; each leaves the trigger failing): hop 3 finds the row with lastIndexOf; hop 4 hands the gold a copy of
the column keys; hop 1 leaves the table unchanged for a null object.
Recorded bypasses (edits that replace or discard the gold's result, not repairs of the chain):
 B-1 hop 4 (or any hop) undoes the gold's append afterwards: `if (columnKeys.indexOf(columnKey) != columnKeys.lastIndexOf(columnKey))
     { columnKeys.remove(columnKeys.size() - 1); }` after the call re-implements the containment rule on the gold's output.
     Checked on the variant in a scratch copy: trigger passes, full suite 0 failing tests.
 B-2 hop 4 passes a throwaway list when the key is known (`columnKeys.contains(columnKey) ? new ArrayList() : columnKeys`): the
     gold's column-key output is made dead on that path.
 B-3 hop 4 stores the object itself when the key is known and skips the gold (`row.setObject(...); return;`).
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.
Masking edit outside the chain (recorded): KeyedObjects2D.removeObject's `this.columnKeys.remove(columnKey)` changed to remove every
copy of the key passes the trigger and the full suite (checked on a scratch copy), but leaves setObject recording a column twice on
every update (getColumnCount() is 3 for a two-column table in the middle of the trigger itself), so setObject and the gold are not
used as documented; it hides one consequence instead of repairing the step.

Lie: the facade's javadoc claims the row keys are kept in sorted order, so that the row for a key is found by a binary search and a
new row is inserted at its sorted position; the chain looks the row up with a linear indexOf and appends a new row at the end. It
names neither column keys, the containment test, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc; `row.setObject(columnKey, object); if (!columnKeys.contains(columnKey)) { columnKeys.add(columnKey); }`):
  T1 absent: object and columnKey are stored by row.setObject; row receives the object; columnKeys is tested and appended to;
     no argument check exists.
  T2 absent: no local variable; the one decision (key not yet present) decides whether the append runs.
  T3 absent: one key list and one row; no enum, type code, pair or range end; the only treatment (containment test) applies to the
     only key list the gold reads.
  T4 absent: 'Stores an object in a row of a table under the given column key' is met by row.setObject; 'makes the column key one
     of the columns of the table' by the append; 'An object that is already stored in the row under that key is replaced' by
     KeyedObjects.setObject; the @param clauses are caller preconditions ('null permitted' for object: row.setObject accepts null).
 Variant gold (javadoc unchanged; body `row.setObject(columnKey, object); columnKeys.add(columnKey);`):
  T1 absent: object and columnKey are passed to row.setObject, columnKey is also appended; row and columnKeys receive writes; all
     four parameters change the side effects.
  T2 absent: no local variable, no loop, no cursor, counter, flag or best-so-far, no literal-initialised value, no branch.
  T3 absent: no member of any set is handled at all ('No member handled': no containment or special-case test remains); the
     gold reads one row and one key list, no pair halves or range ends; the text names no class it handles in part.
  T4 absent: 'Stores an object in a row of a table under the given column key' -> row.setObject(columnKey, object); 'makes the
     column key one of the columns of the table' -> columnKeys.add(columnKey) (a general description the body addresses); 'An
     object that is already stored in the row under that key is replaced' -> KeyedObjects.setObject's replacement; '(<code>null
     </code> permitted)' for object is met (no null test, setObject stores null); the other @param clauses are caller
     preconditions; no inline comment; the identifiers name what they hold."""

KO2 = "source/org/jfree/data/KeyedObjects2D.java"
CP = "source/org/jfree/chart/ChartPanel.java"
SWP = "source/org/jfree/chart/plot/SpiderWebPlot.java"
TP = "source/org/jfree/chart/plot/ThermometerPlot.java"
ACIR = "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java"
AXYIR = "source/org/jfree/chart/renderer/xy/AbstractXYItemRenderer.java"

GOLD_TEXT = '''/**
 * Stores an object in a row of a table under the given column key, and
 * makes the column key one of the columns of the table.  An object that is
 * already stored in the row under that key is replaced.
 *
 * @param object  the object (<code>null</code> permitted).
 * @param columnKey  the column key (<code>null</code> not permitted).
 * @param row  the row (<code>null</code> not permitted).
 * @param columnKeys  the column keys of the table (<code>null</code> not
 *                    permitted).
 */
public static void putObjectInRow(Object object, Comparable columnKey,
        KeyedObjects row, List columnKeys) {
    row.setObject(columnKey, object);
    if (!columnKeys.contains(columnKey)) {
        columnKeys.add(columnKey);
    }
}'''

HOP1 = '''/**
 * Adds or updates an object in a table that is held as a list of row keys,
 * a list of column keys and a list of rows.  An update leaves the existing
 * rows and columns where they are.
 *
 * @param object  the object (<code>null</code> permitted).
 * @param rowKey  the row key (<code>null</code> not permitted).
 * @param columnKey  the column key (<code>null</code> not permitted).
 * @param rowKeys  the row keys of the table.
 * @param columnKeys  the column keys of the table.
 * @param rows  the rows of the table.
 */
public static void addOrUpdateObject(Object object, Comparable rowKey,
        Comparable columnKey, List rowKeys, List columnKeys, List rows) {
    SpiderWebPlot.setObjectInTable(object, rowKey, columnKey, rowKeys,
            columnKeys, rows);
}'''

HOP2 = '''/**
 * Sets an object in a table that is held as a list of row keys, a list of
 * column keys and a list of rows.  An update leaves the existing rows and
 * columns where they are.
 *
 * @param object  the object (<code>null</code> permitted).
 * @param rowKey  the row key (<code>null</code> not permitted).
 * @param columnKey  the column key (<code>null</code> not permitted).
 * @param rowKeys  the row keys of the table.
 * @param columnKeys  the column keys of the table.
 * @param rows  the rows of the table.
 */
public static void setObjectInTable(Object object, Comparable rowKey,
        Comparable columnKey, List rowKeys, List columnKeys, List rows) {
    ThermometerPlot.storeByRowKey(object, rowKey, columnKey, rowKeys,
            columnKeys, rows);
}'''

HOP3 = '''/**
 * Stores an object in the row with the given key, in a table that is held
 * as a list of row keys, a list of column keys and a list of rows.  If the
 * table has no row with that key, a new row is appended to it.  An update
 * leaves the existing rows and columns where they are.
 *
 * @param object  the object (<code>null</code> permitted).
 * @param rowKey  the row key (<code>null</code> not permitted).
 * @param columnKey  the column key (<code>null</code> not permitted).
 * @param rowKeys  the row keys of the table.
 * @param columnKeys  the column keys of the table.
 * @param rows  the rows of the table.
 */
public static void storeByRowKey(Object object, Comparable rowKey,
        Comparable columnKey, List rowKeys, List columnKeys, List rows) {
    KeyedObjects row;
    int rowIndex = rowKeys.indexOf(rowKey);
    if (rowIndex >= 0) {
        row = (KeyedObjects) rows.get(rowIndex);
    }
    else {
        rowKeys.add(rowKey);
        row = new KeyedObjects();
        rows.add(row);
    }
    AbstractCategoryItemRenderer.setRowObject(object, columnKey, row,
            columnKeys);
}'''

HOP4 = '''/**
 * Sets an object in a row of a table under the given column key.  An
 * update leaves the existing columns of the table where they are.
 *
 * @param object  the object (<code>null</code> permitted).
 * @param columnKey  the column key (<code>null</code> not permitted).
 * @param row  the row (<code>null</code> not permitted).
 * @param columnKeys  the column keys of the table.
 */
public static void setRowObject(Object object, Comparable columnKey,
        KeyedObjects row, List columnKeys) {
    AbstractXYItemRenderer.putObjectInRow(object, columnKey, row, columnKeys);
}'''

DESIGN = {
 "instance": "Chart-22", "project": "Chart", "bug_id": 22, "seed": 2296,
 "src_root": "source", "test_root": "tests",
 "facade": {"file": KO2, "class": "org.jfree.data.KeyedObjects2D", "method": "setObject", "near_line": 260},
 "facade_variant": "V1",
 "state_passed": "private fields rowKeys, columnKeys and rows (the List objects) to hop 1, with object, rowKey and columnKey; "
                 "no write-back (the chain appends to the passed lists as the original body did)",
 "reachability_probe": "probe in setObject: full suite 35 failing tests, all java.lang.IllegalStateException: PROBE-REACHED, "
                       "including KeyedObjects2DTests::testRemoveValue (the trigger) and testSetObject; unprobed fixture 0 failing",
 "host_mode": "1500",
 "trigger": {"existing": True, "test_file": "tests/org/jfree/data/junit/KeyedObjects2DTests.java",
             "test_class": "org.jfree.data.junit.KeyedObjects2DTests", "test_method": "testRemoveValue"},
 "expected_signature": "expected:<1> but was:<2>",
 "gold": {"method": "putObjectInRow", "text": GOLD_TEXT,
          "fault": {"old": "        row.setObject(columnKey, object);\n"
                           "        if (!columnKeys.contains(columnKey)) {\n"
                           "            columnKeys.add(columnKey);\n"
                           "        }\n",
                    "new": "        row.setObject(columnKey, object);\n"
                           "        columnKeys.add(columnKey);\n"}},
 "chain": {
   "facade_body": "if (rowKey == null) {\n"
                  "            throw new IllegalArgumentException(\"Null 'rowKey' argument.\");\n"
                  "        }\n"
                  "        if (columnKey == null) {\n"
                  "            throw new IllegalArgumentException(\"Null 'columnKey' argument.\");\n"
                  "        }\n"
                  "        org.jfree.chart.ChartPanel.addOrUpdateObject(object, rowKey, columnKey,\n"
                  "                this.rowKeys, this.columnKeys, this.rows);",
   "lie": "The row keys are kept in sorted order, so the row for a key is found by a binary search and a new row is "
          "inserted at its sorted position.",
   "hops": [
     {"file": CP, "class": "org.jfree.chart.ChartPanel", "method": "addOrUpdateObject",
      "imports": ["java.util.List", "org.jfree.chart.plot.SpiderWebPlot"], "text": HOP1},
     {"file": SWP, "class": "org.jfree.chart.plot.SpiderWebPlot", "method": "setObjectInTable",
      "imports": [], "text": HOP2},
     {"file": TP, "class": "org.jfree.chart.plot.ThermometerPlot", "method": "storeByRowKey",
      "imports": ["java.util.List", "org.jfree.data.KeyedObjects",
                  "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer"], "text": HOP3},
     {"file": ACIR, "class": "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer", "method": "setRowObject",
      "imports": ["org.jfree.data.KeyedObjects", "org.jfree.chart.renderer.xy.AbstractXYItemRenderer"], "text": HOP4},
     {"file": AXYIR, "class": "org.jfree.chart.renderer.xy.AbstractXYItemRenderer", "method": "putObjectInRow",
      "imports": ["org.jfree.data.KeyedObjects"], "gold": True},
   ],
 },
 "evidence": ["org.jfree.data.DefaultKeyedValues2D::setValue",
              "org.jfree.data.KeyedObjects::setObject",
              "org.jfree.data.KeyedObjects2D::getColumnCount"],
 "ownership_reason": "Only the gold records column keys: hops 1, 2 and 4 pass their arguments along unchanged and hop 3 only "
                     "chooses the row (the row with the key, or a new row appended to the table) and never touches the column "
                     "keys. The gold's javadoc promises that the column key is made one of the columns of the table; on an "
                     "update of an object in an existing column the variant appends that key a second time, so the table "
                     "reports a phantom column (getColumnCount() is columnKeys.size()), and removeObject, which removes an "
                     "emptied column key once, leaves it behind. No one-line edit above the gold restores the contract while "
                     "keeping every method used as documented: a hop can keep the gold from appending only by not calling it "
                     "(the object is then not stored, or the hop stores it itself), by handing it another list (the gold's "
                     "column-key output becomes dead), or by removing the key before the call, which moves the column to the "
                     "end of the table on every update, against the hops' javadoc ('An update leaves the existing rows and "
                     "columns where they are'). The convention is pinned outside the gold: DefaultKeyedValues2D.setValue, the "
                     "sibling table of Numbers, appends a column key only when columnKeys.indexOf(columnKey) < 0 "
                     "(DefaultKeyedValues2DTests testRemoveValueBug1690654: the same add / add / remove sequence gives "
                     "getColumnCount() 2 then 1; testColumnCount); KeyedObjects.setObject, the row the gold writes into, "
                     "replaces the object under an existing key instead of adding a second entry (KeyedObjectsTests "
                     "testSetObject); KeyedObjects2D.getColumnCount returns the size of the column-key list.",
 "ownership_tests": ["org.jfree.data.junit.DefaultKeyedValues2DTests::testRemoveValueBug1690654",
                     "org.jfree.data.junit.DefaultKeyedValues2DTests::testColumnCount",
                     "org.jfree.data.junit.KeyedObjectsTests::testSetObject"],
 "compensating": {
   "chain": [
     {"file": TP, "old": "int rowIndex = rowKeys.indexOf(rowKey);",
      "new": "int rowIndex = rowKeys.lastIndexOf(rowKey);",
      "why": "hop 3 finds the row from the end of the row keys"},
     {"file": ACIR, "old": "AbstractXYItemRenderer.putObjectInRow(object, columnKey, row, columnKeys);",
      "new": "AbstractXYItemRenderer.putObjectInRow(object, columnKey, row, new ArrayList(columnKeys));",
      "why": "hop 4 hands the gold a copy of the column keys"},
     {"file": CP, "old": "SpiderWebPlot.setObjectInTable(object, rowKey, columnKey, rowKeys,",
      "new": "if (object == null) { return; } SpiderWebPlot.setObjectInTable(object, rowKey, columnKey, rowKeys,",
      "why": "hop 1 leaves the table unchanged for a null object"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are the recipe's seeded draw `mr_lib.py preview Chart-22 org/jfree/data/KeyedObjects2D.java 5` "
               "with the instance seed 2296 (the draw excludes the facade file KeyedObjects2D.java, the only file in "
               "facade_files_excluded), in draw order, none substituted: ChartPanel (hop 1, 2502 lines), plot.SpiderWebPlot "
               "(hop 2, 1654), plot.ThermometerPlot (hop 3, 1537; the smallest host), renderer.category."
               "AbstractCategoryItemRenderer (hop 4, 1702), renderer.xy.AbstractXYItemRenderer (hop 5, gold, 1750). All five "
               "are public top-level classes in which a static method compiles (the two renderers are abstract, which does not "
               "affect a static method). Anchors from stageB_lib.pick_insertion_anchor with seed 2296 + 100 + i (as mr3_spec.py "
               "inserts them): hop 1 after `getScreenDataArea` (line idx 1951, seed 2396), hop 2 after `setDataset` (372, 2397), "
               "hop 3 after `getUseSubrangePaint` (899, 2398), hop 4 after `setLegendItemLabelGenerator` (1620, 2399), hop 5 "
               "after `getItemLabelGenerator` (314, 2400). The facade calls hop 1 by its fully-qualified name; each hop imports "
               "the next host (SpiderWebPlot and ThermometerPlot share a package) and java.util.List / org.jfree.data."
               "KeyedObjects where the host lacks them. Covariates: host_mode 1500, host sizes 2502/1654/1537/1702/1750, "
               "smallest host 1537 (ThermometerPlot).",
}
