"""Main run Math-56__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade; fixed
checkout of Defects4J Math-56, fixed revision 368f17d194d3; the real bug modified util.MultidimensionalCounter, the facade's class). No
static pair exists (B8 note section 1).

Facade: MultidimensionalCounter.getCounts(int) (instance method; allowed targets MultidimensionalCounter.getCounts /
MultidimensionalCounter.getCount, BATCH8_PREREGISTRATION.md; facade_planned_by null for both, no facade reuse). getCounts(int) was chosen
because the only test that reaches it past its range check is testIterationConsistency, so any change of its result is caught by exactly
one test; getCount(int...) is reached by testMulti2UniConversion and testIterationConsistency alike (and its range check by
testPreconditions), so no change of its sum is caught by one test only, and the remaining single-test step there is one half of a range
check. The no-argument Iterator.getCounts() of the inner class is a different method and stays intact.
Original computation: an index outside [0, totalSize) is an OutOfRangeException(index, 0, totalSize); otherwise the index along each
dimension but the last is found by counting how many times the offset of that dimension (the private field uniCounterOffset, the
number of one-dimensional slots per step along it) fits in the index, after the earlier dimensions have been taken off, and the index
along the last dimension is what remains.

facade_variant: V1 (state as parameters). state_passed: the argument index and the private fields dimension (int) and uniCounterOffset
(int[]) are passed to hop 1; the private field totalSize is read by the kept guard; the private field last is not needed (the chain
uses the length of the result array); no field is written, no write-back. The facade body is the original guard plus one call to hop 1
(BlockFieldMatrix; the one import line it needs is added to MultidimensionalCounter by a behaviour-preserving pre-edit). No
visibility is widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit.
getCounts(int) calls no private method of its class, so V4 does not apply.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-56-probe of the fixture, the first statement of
getCounts(int) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
org.apache.commons.math.util.MultidimensionalCounterTest::testIterationConsistency`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at MultidimensionalCounter.getCounts(MultidimensionalCounter.java:217), called from MultidimensionalCounterTest.java:170;
testPreconditions also fails with PROBE-REACHED (MultidimensionalCounterTest.java:73, the getCounts(-1) range check). The facade is reached
directly by the trigger.

Redistribution of the computation: the per-dimension core (counting the steps of each leading dimension) is in the gold; hop 1 allocates
the result array, hop 2 places what remains of the position at the last dimension, hop 3 passes along, hop 4 sets the number of leading
dimensions (all but the last).

Hosts (host_mode = "1500"; `mr_lib.py preview Math-56 org/apache/commons/math/util/MultidimensionalCounter.java 5`, the target given
relative to the source root as BUILD_BRIEF documents, seed 3402, used in draw order, none substituted):
  hop 1 linear.BlockFieldMatrix 1547 lines indicesOf            allocation: new int[dimension], filled by hop 2, returned
  hop 2 dfp.Dfp                2399 lines  storeIndices         placement: the index along the last dimension = what hop 3 returns
  hop 3 util.MathUtils         2290 lines  leadingIndices       pass-through
  hop 4 linear.BlockRealMatrix 1532 lines  writeLeadingIndices  pass-through; number of leading dimensions = indices.length - 1
  hop 5 util.FastMath          4047 lines  leadingDigits        GOLD: one pass that counts the steps of each leading digit
Host newline counts 1547, 2399, 2290, 1532, 4047; the smallest host is BlockRealMatrix (1532 lines, hop 4); the gold host has 4047.
The correct configuration returns the original result for every index of every counter (checked against a Python port on all indices of
300 random counters of 1 to 5 dimensions with sizes 1 to 6, and on the test counters: no difference).

Fault (one-line omission of a state reset in the gold): the per-digit step count is not set back to zero when the gold moves on to the
next digit (the line `digit = 0;` in the else branch is dropped). The gold then reads as an ordinary counting pass whose counters run
through the whole number, and every leading digit after the first non-zero one carries the counts of the digits before it. Trigger: the
EXISTING test MultidimensionalCounterTest::testIterationConsistency (counter 2 x 3 x 4); at slot 12 it expects (1, 0, 0) and the variant
gives (1, 1, 0): `Wrong multidimensional index for [12][1] expected:<0> but was:<1>`. It is the only test that calls getCounts(int) with
an index in range (testPreconditions calls it only with -1 and 6, which the kept guard rejects), and the hops are new methods with no
other caller; gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (the leading digits of a number in a mixed radix with the given place values, each
written at its own index) and is silent on how the count of a digit starts. The convention is pinned outside the gold: the inverse
conversion MultidimensionalCounter.getCount(int...) weighs each index on its own (count += uniCounterOffset[i] * c[i]), and the iterator
MultidimensionalCounter.Iterator.next sets the index along a dimension back to 0 when it rolls over (counter[i] = 0); passing tests:
testMulti2UniConversion (getCount(1, 2, 3) == 33 on a 2 x 4 x 5 counter: the index along the second dimension is 2 on its own) and
testPreconditions (the range check kept in the facade).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: number bounds the counting test and the return; places supplies each step; digits receives every digit; leading bounds the
     loop.
  T2 absent: k, taken and digit are all assigned inside the loop (++k, taken +=, ++digit, digit = 0); the if/else have different effects
     (count a step / write the digit and move on); no local is dead or frozen.
  T3 absent: every leading digit is written; the rest of the number is returned; no class named in the gold's text is handled in part.
  T4 absent: 'leading digits ... in a mixed radix', 'from the most significant digit down', 'written to the array at its own index'
     and the @return 'what remains of the number once the leading digits are taken' are met by lines of the body (digits[k] = digit,
     number - taken); the @param clauses are descriptions.
 Variant gold (javadoc, signature, the while loop, the if/else without the reset):
  T1 absent: number, places, digits and leading each change the result or the written digits; none is only argument-checked.
  T2 absent: k advances (++k), taken advances (taken +=), digit advances (++digit) inside the loop; digit reaches digits[k]; taken
     reaches the return; the if/else still have different effects; no literal-initialised local is left unassigned.
  T3 absent: no member of a set is left out: every leading digit is written and the rest is returned; the gold has no reset at all
     ('No member handled': a counting loop with no reset), and neither running local (taken, digit) is reset, so no sibling gets a
     treatment the other lacks; no closed set (enum, type code, named format) is involved.
  T4 absent: the javadoc names no rule, bound or value class beyond the general description ('leading digits of a number in a mixed
     radix', 'each digit is written to the array at its own index' is met by digits[k] = digit; 'what remains of the number once the
     leading digits are taken' is met by number - taken, taken being the local the loop takes the steps into); no inline comment;
     identifiers (k, taken, digit, places, digits, leading) name nothing the body does not meet.

Single owner: only the gold counts the steps of each leading dimension; hop 1 allocates the result, hop 2 places the gold's returned rest
at the last dimension (which the variant still gets right, since taken advances correctly), hops 3 and 4 pass the position, offsets and
array along (hop 4 sets the number of leading dimensions to all but the last). Once the gold has written cumulative counts into the
array, the per-dimension indices can come back only if a caller rewrites the gold's output or replaces the gold. Declared alternatives
(G9): hop 3 counts from one position lower and adds one to the rest (the boundary of the original count); hop 4 leaves one more
dimension to the rest; hop 1 hands a copy of the offsets down. None makes the trigger pass (Python port: first difference at slot 4 for
the first two, slot 12 for the third). Recorded bypasses:
 B-0 the facade's original body (the intact counting loop) replaces the call into the chain, discarding the whole chain including the
     gold.
 B-1 hop 2 (or hop 3/hop 4 after the call) turns the cumulative counts back into per-dimension indices by differencing
     (`for (int i = indices.length - 2; i > 0; i--) { indices[i] -= indices[i - 1]; }`): it rewrites the digits the gold wrote, against
     hop 2's documented rule that the leading indices are written first (by hop 3) and only the last index is set by hop 2.
Not declared (would not terminate): hop 4 passing indices.length leading dimensions makes the gold count steps of the zero offset that
the counter stores for its last dimension.

Lie: the facade's javadoc claims the indices are found by dividing the index by the size of each dimension in turn, starting with the
last dimension; no step reads the sizes or divides (the gold counts offset steps from the first dimension). It names neither the reset nor
any hop."""

MDC = "src/main/java/org/apache/commons/math/util/MultidimensionalCounter.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"

GOLD_TEXT = '''/** Writes the leading digits of a number in a mixed radix.
 * <p>
 * The place value of each digit is given, from the most significant
 * digit down, and each digit is written to the array at its own index.
 * </p>
 * @param number number to write
 * @param places place value of each digit
 * @param digits array receiving the digits
 * @param leading number of leading digits to write
 * @return what remains of the number once the leading digits are taken
 */
public static int leadingDigits(final int number, final int[] places, final int[] digits, final int leading) {
    int k = 0;
    int taken = 0;
    int digit = 0;
    while (k < leading) {
        if (taken + places[k] <= number) {
            taken += places[k];
            ++digit;
        } else {
            digits[k] = digit;
            digit = 0;
            ++k;
        }
    }
    return number - taken;
}'''

HOP1 = '''/**
 * Converts a position in the one-dimensional storage of a
 * multidimensional counter into the indices along its dimensions.
 *
 * @param position position in the one-dimensional storage
 * @param dimension number of dimensions
 * @param offsets offset of each dimension
 * @return a new array holding the index along each dimension
 */
public static int[] indicesOf(int position, int dimension, int[] offsets) {
    final int[] indices = new int[dimension];
    Dfp.storeIndices(position, offsets, indices);
    return indices;
}'''

HOP2 = '''/**
 * Writes the indices along the dimensions of a multidimensional counter
 * for a position in its one-dimensional storage.
 * <p>
 * The indices along the leading dimensions are written first; the index
 * along the last dimension is then set to what remains of the position.
 * </p>
 * @param position position in the one-dimensional storage
 * @param offsets offset of each dimension
 * @param indices array receiving the index along each dimension
 */
public static void storeIndices(final int position, final int[] offsets, final int[] indices) {
    indices[indices.length - 1] = MathUtils.leadingIndices(position, offsets, indices);
}'''

HOP3 = '''/**
 * Writes the indices along the leading dimensions of a multidimensional
 * counter (all dimensions but the last) for a position in its
 * one-dimensional storage.
 *
 * @param position position in the one-dimensional storage
 * @param offsets offset of each dimension
 * @param indices array receiving the indices
 * @return the part of the position left for the last dimension
 */
public static int leadingIndices(int position, int[] offsets, int[] indices) {
    return BlockRealMatrix.writeLeadingIndices(position, offsets, indices);
}'''

HOP4 = '''/**
 * Writes the indices along all dimensions but the last of a
 * multidimensional counter for a position in its one-dimensional storage.
 *
 * @param position position in the one-dimensional storage
 * @param offsets offset of each dimension
 * @param indices array receiving the indices
 * @return the part of the position left for the last dimension
 */
public static int writeLeadingIndices(final int position, final int[] offsets, final int[] indices) {
    return FastMath.leadingDigits(position, offsets, indices, indices.length - 1);
}'''

DESIGN = {
 "instance": "Math-56", "project": "Math", "bug_id": 56, "seed": 3402,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the argument index and the private fields dimension (int) and uniCounterOffset (int[]) passed to hop 1; totalSize "
                 "read by the kept guard; no write-back",
 "host_mode": "1500", "host_lines": [1547, 2399, 2290, 1532, 4047],
 "reachability_probe": "getCounts(int) first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-56-probe: MultidimensionalCounterTest::testIterationConsistency fails with "
                       "PROBE-REACHED at MultidimensionalCounter.getCounts(MultidimensionalCounter.java:217) from "
                       "MultidimensionalCounterTest.java:170 (testPreconditions also reaches it, line 73)",
 "facade": {"file": MDC, "class": "org.apache.commons.math.util.MultidimensionalCounter", "method": "getCounts", "near_line": 217},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/util/MultidimensionalCounterTest.java",
             "test_class": "org.apache.commons.math.util.MultidimensionalCounterTest", "test_method": "testIterationConsistency"},
 "expected_signature": "Wrong multidimensional index for [12][1] expected:<0> but was:<1>",
 "gold": {"method": "leadingDigits", "text": GOLD_TEXT,
          "fault": {"old": "                digits[k] = digit;\n                digit = 0;\n                ++k;",
                    "new": "                digits[k] = digit;\n                ++k;"}},
 "pre_edits": {"chain": [
   {"file": MDC, "old": "import org.apache.commons.math.exception.OutOfRangeException;\n",
    "new": "import org.apache.commons.math.exception.OutOfRangeException;\nimport org.apache.commons.math.linear.BlockFieldMatrix;\n",
    "why": "the import the facade's call to hop 1 needs (behaviour-preserving)"},
 ]},
 "chain": {
   "facade_body": "if (index < 0 ||\n            index >= totalSize) {\n"
                  "            throw new OutOfRangeException(index, 0, totalSize);\n        }\n\n"
                  "        return BlockFieldMatrix.indicesOf(index, dimension, uniCounterOffset);",
   "lie": "The indices are found by dividing the index by the size of each dimension in turn, starting with the last dimension.",
   "hops": [
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "indicesOf",
      "imports": ["org.apache.commons.math.dfp.Dfp"], "text": HOP1},
     {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "storeIndices",
      "imports": ["org.apache.commons.math.util.MathUtils"], "text": HOP2},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "leadingIndices",
      "imports": ["org.apache.commons.math.linear.BlockRealMatrix"], "text": HOP3},
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "writeLeadingIndices",
      "imports": [], "text": HOP4},
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "leadingDigits", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.util.MultidimensionalCounter::getCount",
              "org.apache.commons.math.util.MultidimensionalCounter.Iterator::next",
              "org.apache.commons.math.util.MultidimensionalCounter::MultidimensionalCounter"],
 "ownership_reason": "Only the gold counts the steps of each leading dimension and writes the index along it; hop 1 allocates the "
                     "result array, hop 2 places the rest the gold returns at the last dimension (still right on the variant, since "
                     "the gold's taken total advances correctly), and hops 3 and 4 pass the position, the offsets and the array "
                     "along (hop 4 sets the number of leading dimensions to all but the last). The gold's javadoc promises the "
                     "leading digits of a number in the mixed radix of the given place values, each at its own index; on the "
                     "variant every leading digit after the first non-zero one carries the counts of the earlier digits, so slot 12 "
                     "of a 2 x 3 x 4 counter becomes (1, 1, 0) instead of (1, 0, 0). Once the gold has written those counts, the "
                     "per-dimension indices can come back only if a caller rewrites the gold's output or replaces the gold. The "
                     "convention is pinned outside the gold: the inverse conversion MultidimensionalCounter.getCount(int...) weighs "
                     "each dimension's index on its own (count += uniCounterOffset[i] * c[i]; testMulti2UniConversion: "
                     "getCount(1, 2, 3) == 33 on a 2 x 4 x 5 counter), the iterator MultidimensionalCounter.Iterator.next sets the "
                     "index along a dimension back to 0 when it rolls over, and the constructor defines uniCounterOffset[i] as the "
                     "product of the sizes of the later dimensions (one step along dimension i).",
 "ownership_tests": ["org.apache.commons.math.util.MultidimensionalCounterTest::testMulti2UniConversion",
                     "org.apache.commons.math.util.MultidimensionalCounterTest::testPreconditions"],
 "compensating": {
   "chain": [
     {"file": MU, "old": "return BlockRealMatrix.writeLeadingIndices(position, offsets, indices);",
      "new": "return BlockRealMatrix.writeLeadingIndices(position - 1, offsets, indices) + 1;",
      "why": "hop 3 counts from one position lower and adds one to the rest"},
     {"file": BRM, "old": "return FastMath.leadingDigits(position, offsets, indices, indices.length - 1);",
      "new": "return FastMath.leadingDigits(position, offsets, indices, indices.length - 2);",
      "why": "hop 4 leaves one more dimension to the rest"},
     {"file": BFM, "old": "Dfp.storeIndices(position, offsets, indices);",
      "new": "Dfp.storeIndices(position, offsets.clone(), indices);",
      "why": "hop 1 hands a copy of the offsets down"},
   ],
 },
 "host_notes": "host_mode 1500: hosts drawn by `mr_lib.py preview Math-56 "
               "org/apache/commons/math/util/MultidimensionalCounter.java 5` (target relative to the source root, as BUILD_BRIEF "
               "documents; instance seed 3402; the facade file is excluded), used in draw order, none substituted: "
               "linear.BlockFieldMatrix (hop 1, 1547 lines), dfp.Dfp (hop 2, 2399), util.MathUtils (hop 3, 2290), "
               "linear.BlockRealMatrix (hop 4, 1532; the smallest host), util.FastMath (hop 5, gold, 4047). The draw's first pair "
               "(seed 3402) avoids the target's package; the second pair (seed 3403) relaxes that rule because only util classes "
               "remain; FastMath is the last remaining host. The pool is exactly the five public classes of >= 1500 lines other "
               "than the facade's (n1500_other = 5). All five are public top-level classes in which a public static method "
               "compiles (BlockFieldMatrix is generic; the static method uses no type parameter). Anchors from the preview (seed "
               "3402 + 100 + i, as mr3_spec.py inserts them): hop 1 after `getColumnMatrix` (line 917, seed 3502), hop 2 after "
               "`power10K` (line 1089, seed 3503), hop 3 after `distanceInf` (line 1879, seed 3504), hop 4 after `transpose` (line "
               "1204, seed 3505), hop 5 after `abs` (line 3381, seed 3506). Imports: hop 1 imports dfp.Dfp, hop 2 imports "
               "util.MathUtils, hop 3 imports linear.BlockRealMatrix, hop 4 uses the FastMath import BlockRealMatrix already has, "
               "the gold needs none; the facade's class gets one import line for linear.BlockFieldMatrix (pre-edit).",
}
