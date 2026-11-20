"""Main run Math-49__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Math-49, a bug with no static facade; the real bug modified OpenMapRealVector, the facade's class). No static pair (B8 note
section 1).

Facade: OpenMapRealVector.mapAddToSelf(double) (allowed instance target of BATCH8_PREREGISTRATION.md row 290;
facade_planned_by null, no facade reuse). The other two allowed targets were not used, on the reachability probe below:
OpenMapRealVector.hashCode is reached by one existing test only through Object.toString (SparseRealVectorTest::testMisc, which
asserts only that the string is not empty, so no change of the hash value can make a test fail), and
OpenMapRealVector.outerProduct(double[]) is reached by no existing test (the tests call the RealVector overload of
AbstractRealVector).
Original computation of the facade: for every index i below the dimension (the private field virtualSize), the entry is read with
getEntry(i), increased by d and written back with setEntry(i, value) (setEntry stores a value that is not within the zero tolerance
and clears the entry otherwise); the method returns this.

facade_variant: V2 (receiver as parameter). The computation needs only the object's public methods (getDimension, getEntry,
setEntry, sparseIterator): the facade passes `this`, typed as the interface RealVector that OpenMapRealVector implements, and the
argument d to hop 1, and returns this as before. The dimension is read by the chain through getDimension() (which returns the
private field virtualSize); no private field or method is passed or copied (no V1 state, no V4), no package-private type is
involved (no V3/V5). No visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no
reflection, no test edit.
state_passed: the receiver `this` (as RealVector) and the double argument d, handed to hop 1; no write-back (the chain updates the
receiver in place through setEntry, as the original did; the facade returns this).

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in scratch copies of the fixture
(/private/tmp/d4j-mi-Math-49-probe*) the first statement of each allowed facade was made
`if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; full suite (defects4j test) in each:
 mapAddToSelf: 1 failing test, SparseRealVectorTest::testMapFunctions, java.lang.IllegalStateException: PROBE-REACHED at
   OpenMapRealVector.mapAddToSelf(OpenMapRealVector.java:625) called from OpenMapRealVector.mapAdd(OpenMapRealVector.java:619)
   from SparseRealVectorTest.testMapFunctions(SparseRealVectorTest.java:483). It is the only test of the suite that reaches the
   facade (its production callers are mapAdd and AbstractRealVector.mapSubtract / mapSubtractToSelf).
 hashCode: 1 failing test, SparseRealVectorTest::testMisc, PROBE-REACHED at OpenMapRealVector.hashCode(OpenMapRealVector.java:783)
   called from java.lang.Object.toString (assertion: output length != 0 only).
 outerProduct(double[]): 0 failing tests (not reached).

Hosts (host_mode = "1500"; seeded draw `mr_lib.py preview Math-49 org/apache/commons/math/linear/OpenMapRealVector.java 5`, seed
8072, used in draw order, none substituted):
  hop 1 util.FastMath                       4077 lines  addToAll      pass-through
  hop 2 dfp.Dfp                             2489 lines  addScalarTo   pass-through
  hop 3 optimization.direct.BOBYQAOptimizer 3209 lines  addOffset     pass-through
  hop 4 util.MathUtils                      2672 lines  addToSparse   aggregation: marks, index by index, the entries the vector
                                                                      holds (those its sparse iterator returns)
  hop 5 linear.BlockFieldMatrix             1549 lines  addToEntries  GOLD: increases the held entries, then sets each entry that
                                                                      is zero and not held to the value
Host newline counts 4077, 2489, 3209, 2672, 1549; the smallest host (and the gold host) is BlockFieldMatrix (1549 lines).
The correct configuration gives the original result for every vector: each held index i gets getEntry(i) + d through setEntry, as
in the original; each index that is not held has entry 0 (sparseIterator returns every non-zero entry) and gets setEntry(i, d),
which is setEntry(i, 0 + d) of the original; the indices are independent, so the order of the writes does not matter.

Fault (one-line omission of a special-case condition in the gold): the membership test of the second pass is dropped
(`if (v.getEntry(i) == 0 && !held[i]) {` becomes `if (v.getEntry(i) == 0) {`), so the second pass also
sets to the value a held entry that the first pass has just made zero. The gold then reads as the ordinary sparse routine
"increase the held entries, then fill the zero entries with the value". Trigger: the EXISTING test
SparseRealVectorTest::testMapFunctions. mapAdd(2) and mapAddToSelf(2) on {1, 2, 3} still give {3, 4, 5} (no sum is zero), and
v1.mapSubtract(2.0d) (AbstractRealVector.mapSubtract -> mapSubtractToSelf -> mapAddToSelf(-2)) gives {-1, -2, 1} instead of
{-1, 0, 1}: assertClose fails with "compare vectors 1 elements differ expected:<0.0> but was:<-2.0>". It is the only test that
reaches the facade (probe above), and gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract ("Adds a value to the entries of a vector, in place", the held entries first) and
is silent on the second pass; on the trigger the entry 2 - 2 is written as -2, which is not the entry plus the value. The convention
is pinned outside the gold: the intact siblings SparseFieldVector.mapAddToSelf (every entry gets getEntry(i).add(d), a zero sum
included) and ArrayRealVector.mapAddToSelf (data[i] + d for every entry), and the two-pass sparse sibling
OpenMapRealVector.getDistance(OpenMapRealVector), whose second pass picks the remaining entries by membership
(`if (!entries.containsKey(key))`), not by value; passing tests: ArrayRealVectorTest::testMapFunctions and
SparseFieldVectorTest::testMapFunctions (the same {1, 2, 3} - 2 = {-1, 0, 1} on the siblings), SparseRealVectorTest::testPredicates
(an entry set to zero equals a vector built with a zero there) and SparseRealVectorTest::testBasicFunctions (getDistance).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: v is read and written in both passes; held selects the entries of the first pass and decides membership in the
     second; d is added in the first pass and written in the second.
  T2 absent: i is the cursor of both loops and advances; n is a bound read by both loop headers; the first-pass decision
     (held[i]) and the second-pass decision each have two different effects (write / leave the entry); no local is frozen or
     dead.
  T3 absent: held and not-held entries are both treated (increased / set to the value); the two conditions of the second pass are
     both tested; no class named in the gold's text is handled in part.
  T4 absent: 'Adds a value to the entries of a vector, in place' and 'The entries that the vector holds are increased first' are
     met by the two passes; '@param held for each index of the vector, whether the vector holds that entry' describes the input
     (a caller precondition).
 Variant gold (javadoc, signature, the two loops, `if (v.getEntry(i) == 0)`):
  T1 absent: v, held and d each change the result (held selects the entries of the first pass, d is added and written); none
     is only argument-checked.
  T2 absent: i advances in both loops; n is a bound computed before the loops; the decisions `held[i]` and `v.getEntry(i) == 0`
     each write or not; nothing frozen or dead.
  T3 absent: the held entries (first pass) and the zero entries (second pass) are both treated; no closed set has a member left
     out; the gold names no value class.
  T4 absent: 'Adds a value to the entries of a vector, in place' is a general description addressed by both loops; 'The entries
     that the vector holds are increased first' is met by the first loop; '@param held for each index of the vector, whether the
     vector holds that entry' describes the input (Not T4); no inline comment; identifiers (held, n, i) name nothing the body
     does not meet.
 Leakage: the gold needs no import (RealVector is in its own package, the boolean mask needs no library call), so the omitted
 condition leaves no unused import, parameter property or helper behind; hop 4 builds exactly the mask that both passes of the
 gold consume (the variant's first pass still reads it).

Single owner: only the gold writes the entries; hops 1-3 pass (v, d) along and hop 4 only marks the held entries.
The variant refills ANY entry that is zero after the first pass, whatever held contains, so no change of the gold's inputs above it
makes the trigger pass: with every index marked as held (hop 4 reading v.iterator()), the second pass still writes d over the zero
sum; with no index marked, the held entries are not increased at all; a hop cannot restore the overwritten 0 in one line, since the
old value is gone. Declared alternatives (G9): hop 1 skips a zero value; hop 4 marks every entry as held (iterator() for
sparseIterator()); hop 4 marks only the entries whose value is not zero. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold, not repairs of the chain):
 B-0 the facade's original body (or any hop doing `for (int i = 0; i < v.getDimension(); i++) v.setEntry(i, v.getEntry(i) + d);`
     or `v.mapToSelf(FunctionUtils.fix2ndArgument(new Add(), d))` instead of calling on) re-implements the whole computation and
     makes the rest of the chain, including the gold, dead.

Lie: the facade's javadoc claims the entries are first copied into a dense array, the value is added to each element of that array,
and the array is then written back into the vector; no step of the chain copies the entries into an array (hop 4 builds a boolean
mask only, and the gold reads and writes each entry through getEntry / setEntry). It names neither zero entries, the passes, the omitted
step nor any hop. Placement: the facade's javadoc is the one-line `/** {@inheritDoc} */`, separated from the header by @Override,
so rewrite_facade finds no adjacent javadoc; the behaviour-preserving pre-edit (pre_edits.chain) writes that javadoc as a block with
the lie sentence appended after {@inheritDoc}, which is where the recipe appends it. The @Override annotation, the signature and the
modifiers are unchanged."""

OMRV = "src/main/java/org/apache/commons/math/linear/OpenMapRealVector.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"
DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
BOB = "src/main/java/org/apache/commons/math/optimization/direct/BOBYQAOptimizer.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"

LIE = ("The entries are first copied into a dense array, the value is added to each element of that array, and the array "
       "is then written back into the vector.")
# The facade's one-line javadoc `/** {@inheritDoc} */` is separated from its header by @Override, so the recipe's rewrite_facade
# finds no adjacent javadoc to append the lie to; the behaviour-preserving pre-edit below writes the same javadoc as a block
# with the lie sentence appended after {@inheritDoc} (the recipe's placement), wrapped at the class's line width.
LIE_LINES = ("The entries are first copied into a dense array, the value is added to\n"
             "     * each element of that array, and the array is then written back into\n"
             "     * the vector.")

GOLD_TEXT = '''/**
 * Adds a value to the entries of a vector, in place.
 *
 * <p>The entries that the vector holds are increased first.</p>
 *
 * @param v the vector to update
 * @param held for each index of the vector, whether the vector holds
 * that entry
 * @param d the value to add
 */
public static void addToEntries(final RealVector v, final boolean[] held, final double d) {
    final int n = v.getDimension();
    for (int i = 0; i < n; i++) {
        if (held[i]) {
            v.setEntry(i, v.getEntry(i) + d);
        }
    }
    for (int i = 0; i < n; i++) {
        if (v.getEntry(i) == 0 && !held[i]) {
            v.setEntry(i, d);
        }
    }
}'''

HOP1 = '''/**
 * Adds a value to each entry of a vector, in place.
 *
 * @param v vector to update
 * @param d value to add
 */
public static void addToAll(final org.apache.commons.math.linear.RealVector v, final double d) {
    org.apache.commons.math.dfp.Dfp.addScalarTo(v, d);
}'''

HOP2 = '''/**
 * Adds a value to each entry of a vector, in place.
 * @param v vector to update
 * @param d value to add
 */
public static void addScalarTo(final RealVector v, final double d) {
    BOBYQAOptimizer.addOffset(v, d);
}'''

HOP3 = '''/**
 * Adds a value to each entry of a vector, in place.
 *
 * @param v Vector to update.
 * @param d Value to add.
 */
public static void addOffset(final RealVector v, final double d) {
    MathUtils.addToSparse(v, d);
}'''

HOP4 = '''/**
 * Adds a value to each entry of a vector, in place.
 * <p>
 * The entries that the vector holds, those its sparse iterator returns,
 * are marked first.
 * </p>
 *
 * @param v vector to update
 * @param d value to add
 */
public static void addToSparse(final RealVector v, final double d) {
    final boolean[] held = new boolean[v.getDimension()];
    final Iterator<RealVector.Entry> it = v.sparseIterator();
    while (it.hasNext()) {
        held[it.next().getIndex()] = true;
    }
    BlockFieldMatrix.addToEntries(v, held, d);
}'''

DESIGN = {
 "instance": "Math-49", "project": "Math", "bug_id": 49, "seed": 8072,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V2",
 "state_passed": "the receiver this (typed as the interface RealVector) and the argument d, passed to hop 1; no field passed, "
                 "no write-back (the chain updates the receiver in place through setEntry; the facade returns this)",
 "host_mode": "1500", "host_lines": [4077, 2489, 3209, 2672, 1549],
 "reachability_probe": "mapAddToSelf first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-49-probe-mapadd: full suite 1 failing test, "
                       "SparseRealVectorTest::testMapFunctions, PROBE-REACHED at OpenMapRealVector.mapAddToSelf"
                       "(OpenMapRealVector.java:625) via mapAdd (:619) from SparseRealVectorTest.java:483; hashCode probe: only "
                       "SparseRealVectorTest::testMisc via Object.toString (no value assertion); outerProduct(double[]) probe: "
                       "0 failing tests",
 "facade": {"file": OMRV, "class": "org.apache.commons.math.linear.OpenMapRealVector", "method": "mapAddToSelf", "near_line": 624},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/linear/SparseRealVectorTest.java",
             "test_class": "org.apache.commons.math.linear.SparseRealVectorTest", "test_method": "testMapFunctions"},
 "expected_signature": "1 elements differ expected:<0.0> but was:<-2.0>",
 "gold": {"method": "addToEntries", "text": GOLD_TEXT,
          "fault": {"old": "            if (v.getEntry(i) == 0 && !held[i]) {",
                    "new": "            if (v.getEntry(i) == 0) {"}},
 "chain": {
   "facade_body": "FastMath.addToAll(this, d);\n        return this;",
   "lie": LIE,
   "hops": [
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "addToAll", "imports": [], "text": HOP1},
     {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "addScalarTo",
      "imports": ["org.apache.commons.math.linear.RealVector",
                  "org.apache.commons.math.optimization.direct.BOBYQAOptimizer"], "text": HOP2},
     {"file": BOB, "class": "org.apache.commons.math.optimization.direct.BOBYQAOptimizer", "method": "addOffset",
      "imports": ["org.apache.commons.math.linear.RealVector"], "text": HOP3},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "addToSparse",
      "imports": ["java.util.Iterator", "org.apache.commons.math.linear.RealVector",
                  "org.apache.commons.math.linear.BlockFieldMatrix"], "text": HOP4},
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "addToEntries",
      "imports": [], "gold": True},
   ],
 },
 "pre_edits": {"chain": [
   {"file": OMRV,
    "old": "    /** {@inheritDoc} */\n    @Override\n    public OpenMapRealVector mapAddToSelf(double d) {",
    "new": "    /**\n     * {@inheritDoc}\n     * " + LIE_LINES + "\n     */\n    @Override\n"
           "    public OpenMapRealVector mapAddToSelf(double d) {"},
 ]},
 "evidence": ["org.apache.commons.math.linear.SparseFieldVector::mapAddToSelf",
              "org.apache.commons.math.linear.ArrayRealVector::mapAddToSelf",
              "org.apache.commons.math.linear.OpenMapRealVector::getDistance"],
 "ownership_reason": "Only the gold writes the entries of the vector: it increases the entries the vector holds and then sets "
                     "each remaining zero entry to the value. Hops 1-3 pass the vector and the value along; hop 4 only marks "
                     "the held entries (its sparse iterator). Without the membership test, the "
                     "gold's second pass also writes the value over a held entry that its own first pass has just made zero, "
                     "whatever mask it is given, so no caller can pre-filter or restore it (the old value is gone). The "
                     "gold's javadoc promises that the value is added to the entries; on the trigger 2 - 2 is written as -2. "
                     "The convention is pinned outside the gold: SparseFieldVector.mapAddToSelf and ArrayRealVector.mapAddToSelf "
                     "add the value to every entry, a zero sum included, and the two-pass sparse sibling "
                     "OpenMapRealVector.getDistance(OpenMapRealVector) picks the remaining entries of its second pass by "
                     "membership (containsKey), not by value; ArrayRealVectorTest::testMapFunctions and "
                     "SparseFieldVectorTest::testMapFunctions (the same {1, 2, 3} - 2 = {-1, 0, 1}), "
                     "SparseRealVectorTest::testPredicates and SparseRealVectorTest::testBasicFunctions pass.",
 "ownership_tests": ["org.apache.commons.math.linear.ArrayRealVectorTest::testMapFunctions",
                     "org.apache.commons.math.linear.SparseFieldVectorTest::testMapFunctions",
                     "org.apache.commons.math.linear.SparseRealVectorTest::testPredicates",
                     "org.apache.commons.math.linear.SparseRealVectorTest::testBasicFunctions"],
 "compensating": {
   "chain": [
     {"file": FM, "old": "org.apache.commons.math.dfp.Dfp.addScalarTo(v, d);",
      "new": "if (d != 0) { org.apache.commons.math.dfp.Dfp.addScalarTo(v, d); }",
      "why": "hop 1 skips a zero value"},
     {"file": MU, "old": "final Iterator<RealVector.Entry> it = v.sparseIterator();",
      "new": "final Iterator<RealVector.Entry> it = v.iterator();",
      "why": "hop 4 marks every entry of the vector as held"},
     {"file": MU, "old": "held[it.next().getIndex()] = true;",
      "new": "final RealVector.Entry e = it.next(); if (e.getValue() != 0) { held[e.getIndex()] = true; }",
      "why": "hop 4 marks only the held entries whose value is not zero"},
   ],
 },
 "host_notes": "host_mode 1500: seeded draw of mr_lib.py preview Math-49 org/apache/commons/math/linear/OpenMapRealVector.java 5 "
               "(seed 8072; the facade's file OpenMapRealVector.java, the only allowed candidates' file, is excluded), used in "
               "draw order, none substituted: util.FastMath (hop 1, 4077 lines), dfp.Dfp (hop 2, 2489), "
               "optimization.direct.BOBYQAOptimizer (hop 3, 3209), util.MathUtils (hop 4, 2672), linear.BlockFieldMatrix "
               "(hop 5, gold, 1549; the smallest host; the draw relaxed package distinctness for hop 5, pool of 2). All five are "
               "public concrete top-level classes in which a public static method compiles (BlockFieldMatrix is generic; the "
               "gold is a static non-generic method). Anchors (preview, seed 8072 + 100 + i): hop 1 after ceil (8172), hop 2 "
               "after newInstance (8173), hop 3 after the BOBYQAOptimizer constructor (8174), hop 4 after addAndCheck (8175), "
               "hop 5 after createMatrix (8176). FastMath has no import statements, so hop 1 names RealVector and Dfp by their "
               "fully-qualified names; the facade calls hop 1 as FastMath.addToAll (OpenMapRealVector already imports "
               "util.FastMath); the other hops import the next host and RealVector / java.util.Iterator as needed; the gold, in "
               "the package of RealVector, adds no import.",
}
