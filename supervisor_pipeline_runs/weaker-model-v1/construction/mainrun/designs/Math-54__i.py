"""Main run Math-54__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug with no static facade; fixed
checkout of Defects4J Math-54, whose real bug modified org.apache.commons.math.dfp.Dfp, the facade's class). No static pair
(BUILD_BRIEF_C10I_B8_NOTE.md section 1).

Facade: Dfp.log10() (instance method; the only allowed candidate of batch8_tasks.json, BATCH8_PREREGISTRATION.md row 292;
facade_planned_by null, no facade reuse).
Original computation: with w = mant[mant.length - 1] (the most significant radix-10000 word) and exp (the word exponent; the number
is w * 10000^(exp - 1) plus the lower words), the result is exp * 4 - 1 if w > 1000, exp * 4 - 2 if w > 100, exp * 4 - 3 if w > 10,
and exp * 4 - 4 otherwise, i.e. 4 * (exp - 1) plus the decimal exponent of the leading word. Production callers: Dfp.toDouble (first
estimate of the binary exponent, then adjusted upwards by a doubling loop) and DfpDec.nextAfter (the size of one unit in the last
place).

facade_variant: V1 (state as parameters). state_passed: the protected fields mant (int[]) and exp (int) of the receiver, passed to
hop 1; no field is written, no write-back. The facade body is one call to hop 1 (the original had no guard). The computation needs no
method of the receiver (V2 not needed), calls no private method (no V4) and involves no package-private type (no V3/V5). No visibility
is widened, no type is added, no signature, modifier, override or throws clause changes, no reflection, no test edit.

reachability_probe (C10i addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-54-probe of the fixture, the first
statement of log10() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
`defects4j test -t org.apache.commons.math.dfp.DfpTest::testLog10`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED
(the test calls log10() directly); `defects4j test -t org.apache.commons.math.dfp.DfpDecTest::testNextAfter`: 1 failing test,
PROBE-REACHED at Dfp.log10(Dfp.java:1099) from DfpDec.nextAfter(DfpDec.java:323) from DfpDecTest.testNextAfter(DfpDecTest.java:504).
The facade is reached by existing tests. An instrumented scratch copy (log10 recording its inputs) over the full suite: 73041 calls,
from DfpTest::testLog10 (16), DfpDecTest::testNextAfter (12) and 19 FastMathTest accuracy tests (through Dfp.toDouble).

Hosts (host_mode = "largest5"; batch8_tasks.json hosts_hop_order, used in that order, none substituted):
  hop 1 util.FastMath                         4047 lines  decimalExponent     plumbing: takes the most significant word
  hop 2 util.MathUtils                        2326 lines  leadingWordExponent placement: the decimal exponent 4 * (exp - 1) of the
                                                                              units digit of the leading word
  hop 3 linear.BlockFieldMatrix               1547 lines  exponentFromOffset  pass-through
  hop 4 linear.BlockRealMatrix                1532 lines  offsetExponent      aggregation: the offset plus the word's own exponent
  hop 5 optimization.direct.CMAESOptimizer    1300 lines  digitExponent       GOLD: the decimal exponent of one word (its leading
                                                                              decimal digit), from its bit length
Host newline counts 4047, 2326, 1547, 1532, 1300; the smallest host (and the gold host) is CMAESOptimizer with 1300 lines (C10F
addendum section 1: hosts under 1500 lines are expected in this regime).
The correct configuration returns the original result for every word except the exact powers 10, 100 and 1000, for which the
original's strict comparisons give one less than the exponent of the greatest power of ten not above the number (the facade's own
javadoc); the chain returns that exponent (checked in Python for every word 1..9999: the bit-length estimate plus its correction
equals floor(log10(word))). For a zero word (the Dfp zero) the chain gives 4 * (exp - 1) - 1 instead of exp * 4 - 4; the only
caller that reaches log10() with zero, DfpDec.nextAfter, replaces the increment it derives from it for a zero receiver. Dfp.toDouble
only uses the result as a first estimate below the binary exponent, and its doubling loop finds the same exponent for any estimate
that is not too high; the chain's estimate is never higher than the true decimal exponent.

Fault (one-line omission of a special-case decision in the gold): the correction of the bit-length estimate is dropped (the
`if (value >= MathUtils.pow(10, exponent + 1)) { exponent++; }` block), so a word at or above the next power of ten within its bit
length (10..15, 100..127, 1000..1023) gets an exponent one too small. The gold then reads as the ordinary routine "the decimal
exponent from the bit length". Trigger: the EXISTING test DfpTest::testLog10; its first assertion, assertEquals("log10 #1", 1,
field.newDfp("12").log10()), fails with expected:<1> but was:<0>. It is the only test that newly fails: DfpDecTest::testNextAfter
reaches log10() only with the leading words 1, 9999, 999 and 0 (the instrumented run), outside the corrected ranges, and the
FastMathTest accuracy tests reach it through Dfp.toDouble, whose doubling loop absorbs an estimate that is too small.

The gold's javadoc states the idiomatic contract (the decimal exponent of a positive value, the exponent of its leading decimal
digit) and is silent on how the bit length is turned into it; the leading decimal digit of 12 is in the tens place, exponent 1, and
the variant returns 0. The convention is pinned outside the gold: Dfp.dfp2sci writes the scientific exponent as the exponent of the
leading decimal digit (`e = exp * 4 - shf - 1`, shf = the number of leading zero digits), Dfp.power10 is the inverse (10^e), and the
facade's own javadoc ("the greatest power of 10 that is less than or equal to abs(this)"); passing tests: DfpTest::testToString
("1.2300000000000000e100", "12345678.1234", "0.00001234"), DfpTest::testPower10, DfpDecTest::testNextAfter (through the chain: the
exponents of 1, 0.99999999999999999 and 9.9999999999999999e131078).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, estimate line, the correction if-block, return):
  T1 absent: value is the only parameter and determines the estimate and the correction.
  T2 absent: exponent is computed (not a literal), read by the correction and returned; the correction decision changes the result
     for 10..15, 100..127, 1000..1023; no dead or frozen local.
  T3 absent: no enumeration, no set of cases or parallel branches; one decision.
  T4 absent: 'the decimal exponent of the value, that is the exponent of the leading decimal digit of the value' is met by the
     body; 'Positive value' is a caller precondition.
 Variant gold (javadoc, signature, `int exponent = ((31 - Integer.numberOfLeadingZeros(value)) * 1233) >> 12;`, `return exponent;`):
  T1 absent: value determines the result through its bit length.
  T2 absent: exponent is initialised from value (not a literal) and returned; no loop, no branch, no ternary, so no frozen cursor
     and no dead decision.
  T3 absent: no set of members is handled in part: no branch, case, check or key; no class named in the gold's text is partly
     handled.
  T4 absent: the javadoc and @return describe what the method computes in general ('the decimal exponent of the value, that is the
     exponent of the leading decimal digit'), which the estimate line addresses; '@param value Positive value.' is a caller
     precondition; no inline comment; identifiers (value, exponent, digitExponent) name nothing the body does not meet.

Single owner: only the gold turns a word into its decimal exponent; hop 1 picks the most significant word, hop 2 computes the decimal
offset of the word's units digit, hop 3 passes both along, hop 4 adds the offset to the gold's result. The word's own exponent is decided
nowhere else, so once the gold has returned 0 for the word 12, the 1 can appear only if a caller recomputes the word's exponent itself or
replaces the gold. Declared alternatives (G9): hop 2 places the units digit one decimal place higher; hop 1 passes ten times the leading
word; hop 4 passes the word plus one. None makes the trigger pass (the first breaks "1234" -> 3, the other two keep "12" -> 0).
Recorded bypasses: B-0 the facade's original body (the three comparisons) discards the chain; B-1 hop 4 (or any hop) computes the word's
exponent itself, e.g. `offset + (int) FastMath.floor(FastMath.log10(word))`, discarding the gold's output; B-2 hop 4 adds the
correction to the gold's result (`if (word >= MathUtils.pow(10, e + 1)) e++`), a second implementation of the gold's decision.

Lie: the facade's javadoc claims the mantissa is first written out as a string of decimal digits and the exponent is read from the
position of its first non-zero digit; no step of the chain writes digits out (the gold works from the bit length of one word). It
names neither the correction nor any hop."""

DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"
MU = "src/main/java/org/apache/commons/math/util/MathUtils.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"
CMA = "src/main/java/org/apache/commons/math/optimization/direct/CMAESOptimizer.java"

GOLD_TEXT = '''/**
 * @param value
 *            Positive value.
 * @return the decimal exponent of the value, that is the exponent of the
 *         leading decimal digit of the value.
 */
public static int digitExponent(final int value) {
    int exponent = ((31 - Integer.numberOfLeadingZeros(value)) * 1233) >> 12;
    if (value >= MathUtils.pow(10, exponent + 1)) {
        exponent++;
    }
    return exponent;
}'''

HOP1 = '''/** Compute the decimal exponent of a number held in radix 10000 words.
 * <p>Each word holds four decimal digits, the most significant word last;
 * the most significant word stands for itself times 10000 raised to the
 * power {@code wordExponent - 1}.</p>
 * @param words the words of the number, most significant last
 * @param wordExponent exponent of the number, in powers of 10000
 * @return the exponent of the leading decimal digit of the number
 */
public static int decimalExponent(final int[] words, final int wordExponent) {
    return MathUtils.leadingWordExponent(words[words.length - 1], wordExponent);
}'''

HOP2 = '''/**
 * Returns the exponent of the leading decimal digit of a number, given its
 * most significant radix 10000 word.
 *
 * @param leadingWord the most significant word of the number.
 * @param wordExponent the exponent of the number, in powers of 10000; the
 * units digit of the leading word stands for 10 raised to the power
 * {@code 4 * (wordExponent - 1)}.
 * @return the exponent of the leading decimal digit of the number.
 */
public static int leadingWordExponent(final int leadingWord, final int wordExponent) {
    return BlockFieldMatrix.exponentFromOffset(leadingWord, 4 * (wordExponent - 1));
}'''

HOP3 = '''/**
 * Get the decimal exponent of the leading digit of a word placed at a
 * decimal offset.
 * @param word word holding up to four decimal digits
 * @param offset decimal exponent of the units digit of the word
 * @return decimal exponent of the leading digit of the word
 */
public static int exponentFromOffset(final int word, final int offset) {
    return BlockRealMatrix.offsetExponent(word, offset);
}'''

HOP4 = '''/**
 * Get the decimal exponent of the leading digit of a word placed at a
 * decimal offset.
 * <p>The offset is added to the decimal exponent of the word itself.</p>
 * @param word word holding up to four decimal digits
 * @param offset decimal exponent of the units digit of the word
 * @return decimal exponent of the leading digit of the word
 */
public static int offsetExponent(final int word, final int offset) {
    return offset + CMAESOptimizer.digitExponent(word);
}'''

DESIGN = {
 "instance": "Math-54", "project": "Math", "bug_id": 54, "seed": 4408,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the protected fields mant (int[]) and exp (int) of the receiver, passed to hop 1; no write-back",
 "host_mode": "largest5", "host_lines": [4047, 2326, 1547, 1532, 1300],
 "reachability_probe": "log10() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-54-probe: DfpTest::testLog10 fails with PROBE-REACHED (direct call) and "
                       "DfpDecTest::testNextAfter fails with PROBE-REACHED at Dfp.log10(Dfp.java:1099) via DfpDec.nextAfter",
 "facade": {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "log10", "near_line": 1098},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/dfp/DfpTest.java",
             "test_class": "org.apache.commons.math.dfp.DfpTest", "test_method": "testLog10"},
 "expected_signature": "log10 #1 expected:<1> but was:<0>",
 "gold": {"method": "digitExponent", "text": GOLD_TEXT,
          "fault": {"old": "        int exponent = ((31 - Integer.numberOfLeadingZeros(value)) * 1233) >> 12;\n"
                           "        if (value >= MathUtils.pow(10, exponent + 1)) {\n"
                           "            exponent++;\n"
                           "        }\n"
                           "        return exponent;",
                    "new": "        int exponent = ((31 - Integer.numberOfLeadingZeros(value)) * 1233) >> 12;\n"
                           "        return exponent;"}},
 "chain": {
   "facade_body": "return org.apache.commons.math.util.FastMath.decimalExponent(mant, exp);",
   "lie": "The mantissa is first written out as a string of decimal digits, and the exponent is read from the position of its "
          "first non-zero digit.",
   "hops": [
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "decimalExponent",
      "imports": [], "text": HOP1},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "leadingWordExponent",
      "imports": ["org.apache.commons.math.linear.BlockFieldMatrix"], "text": HOP2},
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "exponentFromOffset",
      "imports": [], "text": HOP3},
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "offsetExponent",
      "imports": ["org.apache.commons.math.optimization.direct.CMAESOptimizer"], "text": HOP4},
     {"file": CMA, "class": "org.apache.commons.math.optimization.direct.CMAESOptimizer", "method": "digitExponent",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.dfp.Dfp::dfp2sci",
              "org.apache.commons.math.dfp.Dfp::power10",
              "org.apache.commons.math.dfp.DfpDec::nextAfter"],
 "ownership_reason": "Only the gold turns a word into its decimal exponent (the exponent of its leading decimal digit). Hop 1 picks "
                     "the most significant word of the mantissa, hop 2 computes the decimal exponent 4 * (exp - 1) of that word's "
                     "units digit, hop 3 passes word and offset along, and hop 4 adds the offset to the gold's result; no other step "
                     "looks at the digits of the word. Once the gold has returned 0 for the word 12, the exponent 1 of the number 12 "
                     "can appear only if a caller recomputes the word's exponent itself or replaces the gold. The gold's javadoc "
                     "promises the exponent of the leading decimal digit; the leading digit of 12 is in the tens place. The "
                     "convention is pinned outside the gold: Dfp.dfp2sci writes the scientific exponent as the exponent of the "
                     "leading decimal digit (e = exp * 4 - shf - 1, shf the number of leading zero digits), Dfp.power10 is the "
                     "inverse (10^e), and the facade's own javadoc names the greatest power of 10 not above abs(this); "
                     "DfpTest::testToString (scientific exponent 100 of 1.23e100) and DfpTest::testPower10 pass, and "
                     "DfpDecTest::testNextAfter passes through the chain (the exponents of 1, 0.99999999999999999 and "
                     "9.9999999999999999e131078 fix the size of one unit in the last place).",
 "ownership_tests": ["org.apache.commons.math.dfp.DfpTest::testToString",
                     "org.apache.commons.math.dfp.DfpTest::testPower10",
                     "org.apache.commons.math.dfp.DfpDecTest::testNextAfter"],
 "compensating": {
   "chain": [
     {"file": MU, "old": "return BlockFieldMatrix.exponentFromOffset(leadingWord, 4 * (wordExponent - 1));",
      "new": "return BlockFieldMatrix.exponentFromOffset(leadingWord, 4 * wordExponent - 3);",
      "why": "hop 2 places the units digit of the leading word one decimal place higher"},
     {"file": FM, "old": "return MathUtils.leadingWordExponent(words[words.length - 1], wordExponent);",
      "new": "return MathUtils.leadingWordExponent(words[words.length - 1] * 10, wordExponent);",
      "why": "hop 1 passes ten times the leading word"},
     {"file": BRM, "old": "return offset + CMAESOptimizer.digitExponent(word);",
      "new": "return offset + CMAESOptimizer.digitExponent(word + 1);",
      "why": "hop 4 passes the word plus one"},
   ],
 },
 "host_notes": 'host_mode largest5 (batch8_tasks.json hosts_hop_order, used in that order; none substituted, none drawn by this builder): util.FastMath (hop 1, 4047 lines), util.MathUtils (hop 2, 2326), linear.BlockFieldMatrix (hop 3, 1547), linear.BlockRealMatrix (hop 4, 1532), optimization.direct.CMAESOptimizer (hop 5, gold, 1300; the smallest host). All five are public concrete top-level classes in which a public static method compiles (BlockFieldMatrix is generic; the static hop uses no type parameter); the facade file dfp/Dfp.java is excluded. Anchors from stageB_lib.insert_hop (pick_insertion_anchor) with seed 4408 + 100 + i, as mr3_spec.py inserts them: hop 1 after sin (seed 4508), hop 2 after distance (4509), hop 3 after getRowVector (4510), hop 4 after scalarAdd (4511), hop 5 after getStatisticsDHistory (4512). The facade calls hop 1 by its fully-qualified name; MathUtils imports linear.BlockFieldMatrix, BlockRealMatrix imports optimization.direct.CMAESOptimizer; FastMath -> MathUtils and BlockFieldMatrix -> BlockRealMatrix are same-package calls; CMAESOptimizer already imports util.MathUtils (used by the gold for MathUtils.pow).',
}
