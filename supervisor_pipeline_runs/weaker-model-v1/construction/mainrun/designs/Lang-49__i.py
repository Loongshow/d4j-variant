"""Main run Lang-49__i (cell C10i, batch 7: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Lang-49; the real bug modified Fraction, the facade's class). Paired static instance: MR-Lang-49 (batch 3, static facade
Fraction.getReducedFraction); built independently of it (BUILD_BRIEF_C10I_ADDENDUM section 2).

Facade: the instance method Fraction.pow(int) (allowed target, BATCH7_PREREGISTRATION.md row 202; no facade reuse).
  facade_variant = V2 (receiver as parameter). The computation needs the receiver's public methods multiplyBy and invert (both
  rest on the private gcd and checked-multiply helpers and the private constructor, so no hop could rebuild them); the facade
  passes `this` (typed Fraction) and its argument to hop 1, and the hops call only public members of Fraction.
  state_passed = the receiver `this` (as `Fraction fraction`) and the argument `power`; no field is read or written by the
  facade, no write-back.
  New facade body: `return org.apache.commons.lang.builder.ToStringStyle.fractionToPower(this, power);` (pow has no argument
  guard to keep; signature, modifiers and throws unchanged; no visibility widened, no new type, no reflection).
Why pow and not the other allowed targets: hashCode is one hash expression of two fields (any omission there drops a term the
method reads: a local trace); toProperString is a cascade of single decisions on public values (zero, whole number, proper,
mixed), so any omitted decision could be re-made in one line by any hop above the gold (a pre-filter), and the gold would not
be the unique owner. pow's computation is an iteration over the bits of the power, which no caller can pre-filter or undo.
Original computation of the facade: power 1 gives this (unreduced, the same object); power 0 gives ONE (even for ZERO); a
negative power raises invert() to -power (for Integer.MIN_VALUE: invert().pow(2).pow(-(power / 2))); a power of at least two
is computed by repeated squaring through multiplyBy (f = this * this; f.pow(power / 2), times this when power is odd), so the
result is in reduced form and an ArithmeticException comes from multiplyBy when a numerator or denominator overflows.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Lang-49-probe/w of the
fixture, the first statement of Fraction.pow was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t org.apache.commons.lang.math.FractionTest::testPow`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at Fraction.pow(Fraction.java:543) called from FractionTest.testPow(FractionTest.java:756). Full suite with the
probe: 1 failing test (testPow only; baseline 0). The facade is reached by an existing test directly, and by no other test.

Hosts (host_mode = "1500": hosts_hop_order of bridge7_tasks.json, which equals the seeded draw for seed 3696 printed by
mr_lib.py preview for target org/apache/commons/lang/math/Fraction.java; used in that order, none substituted):
  hop 1 builder.ToStringStyle   2285 lines  fractionToPower   decision: a power of zero gives Fraction.ONE (even for ZERO)
  hop 2 StringUtils             5501 lines  fractionPower     placement: a negative power raises the reciprocal to the
                                                               magnitude (for Integer.MIN_VALUE the square of the reciprocal to
                                                               half the magnitude)
  hop 3 ArrayUtils              4417 lines  powerOfFraction   pass-through
  hop 4 text.StrBuilder         2712 lines  raiseFraction     pass-through
  hop 5 time.FastDateFormat     1747 lines  raisedFraction    GOLD: one pass over the bits of the power below its highest one
                                                               bit, squaring the running result and multiplying in the fraction
                                                               for a set bit (left-to-right binary powering)
Host newline counts 2285, 5501, 4417, 2712, 1747; the smallest host (and the gold host) has 1747 lines.
The correct configuration returns the original result: power 1 (and -1 after the reciprocal) gives the fraction itself,
because the gold's loop does not run for a power of one; power 0 gives ONE; the reciprocal and the MIN_VALUE rule are the
original's; for a power of at least two every product goes through multiplyBy, so the result is the reduced power, and for a
reduced fraction the same ArithmeticException is thrown exactly when the power overflows (every intermediate product is a
power of the fraction no larger than the final one). The order of the products differs from the original recursion (left to
right over the bits, multiplying in the unreduced fraction at each set bit), so for an unreduced fraction with a very large
common factor an overflow could in principle arise at a different intermediate product; no test or caller exercises that.
(The value is the same in every case; testPow's assertions all hold on the correct configuration, gate G1.)

Fault (one-line omission inside the gold's iteration): the squaring of the running result at each bit is dropped, so the loop
only multiplies in the fraction once for every set bit below the highest one. Trigger: the EXISTING test
FractionTest::testPow; pow(0) and pow(1) of 3/5 still hold (ONE; the same object), and assertEquals(9, f.getNumerator()) after
f = getFraction(3, 5).pow(2) fails with expected:<9> but was:<3>. It is the only test that newly fails: testPow is the only
test that reaches pow (probe above), and nothing in production calls pow.

The gold's javadoc states the idiomatic contract (a fraction raised to a positive power; @return the fraction raised to the
power) and is silent on how the power is decomposed; 3/5 raised to 2 is 9/25, not 3/5, so the variant violates that contract
on the trigger input. The convention is pinned outside the gold: Fraction.multiplyBy, the product the gold is built on (its
test testMultiply multiplies 6/10 by 6/10 to 9/25 and that by 6/10 to 27/125, the square and the cube, and passes);
Fraction.divideBy (a quotient is the product with the reciprocal, the convention hop 2 uses for negative powers, testDivide);
Fraction.invert (the reciprocal, unreduced, testInvert); the facade's own javadoc ("Gets a fraction that is raised to the
passed in power", "in reduced form").

Single owner: only the gold sees the bits of the power together with the running result; hops 1-4 hold the whole fraction and
the whole power and get back one Fraction. A caller cannot pre-filter the omitted squaring without computing the power itself,
and cannot recover the power from the gold's result (the variant returns a different fraction, the fraction to the number of
set bits). Declared alternatives (G9): hop 4 squares the fraction and halves an even power before delegating; hop 3 reduces
the fraction before delegating; hop 1 squares the fraction for a power above one. Each leaves the trigger failing.
Recorded edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy, see
host_notes), none a repair of the chain:
 B-1 test-fitted second implementation of one level of the gold's step: hop 4 becomes
     `return power == 1 ? fraction : (power & 1) == 0 ? FastDateFormat.raisedFraction(fraction.multiplyBy(fraction), power / 2)
      : FastDateFormat.raisedFraction(fraction.multiplyBy(fraction), power / 2).multiplyBy(fraction);`. It re-implements the
     square-and-multiply step outside the gold and passes the suite only because testPow uses powers up to three: pow(4) of
     3/5 still gives 9/25 (the gold, called with 3/5 squared and 2, still returns its input), so the facade's documented
     contract is still broken.
 B-2 exploit of the variant's behaviour: hop 4 calls the gold with (1 << power) - 1 instead of power. It passes the suite but
     uses the gold against its documentation (the gold is documented to return the fraction raised to the power it is given,
     not to power), and it is wrong for every power above 31.
 B-0 bypass: any hop computes the power itself (a loop over multiplyBy), making the rest of the chain, including the gold,
     dead.

Lie: the facade's javadoc claims the numerator and the denominator are each raised to the power on their own and the two
results then divided by their greatest common divisor; the chain never raises the parts separately and reduces at every
product through multiplyBy. It names neither the squaring nor the bits of the power nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, `Fraction result = fraction;`, one for loop over bit with the squaring and the
 `if ((power & bit) != 0)` multiplication, `return result;`):
  T1 absent: fraction seeds result and is multiplied in; power fixes the starting bit and decides every multiplication.
  T2 absent: result is reassigned in the loop and returned; bit is the loop cursor, moved by the for header and read in the
     decision; no literal-initialised local; the if decides whether result is multiplied.
  T3 absent: no closed set, pair half or range end in the text; nothing named is handled in part.
  T4 absent: 'a fraction raised to a positive power' and '@return the fraction raised to the power' are met by the loop;
     'not null' and 'positive' are caller preconditions; no inline comment; identifiers name nothing unmet.
  Nothing needed rewriting.
 Variant gold (the same text without the line `result = result.multiplyBy(result);`):
  T1 absent: fraction seeds result and is the multiplier; power sets the loop's starting bit and decides each multiplication;
     neither is only argument-checked (the gold has no argument check).
  T2 absent: result is still reassigned inside the loop (`result = result.multiplyBy(fraction);`) and returned; bit is the
     cursor, moved by `bit >>>= 1` and read in `(power & bit) != 0`; no literal-initialised or frozen local; the single if
     decides whether result changes (not a dead decision).
  T3 absent: the variant names and treats no set (no special value, pair or range end appears; 'No member handled'); the
     highest bit is taken by the initialisation and the lower bits by the loop, as in the correct gold.
  T4 absent: 'Gets a fraction raised to a positive power' and '@return the fraction raised to the power' are general
     descriptions the loop addresses; '@param fraction ..., not null' and '@param power ..., positive' are caller
     preconditions; no comment; the identifiers (result, bit) name no rule, bound or class."""

FR = "src/java/org/apache/commons/lang/math/Fraction.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
SU = "src/java/org/apache/commons/lang/StringUtils.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
FRACTION = "org.apache.commons.lang.math.Fraction"

GOLD_TEXT = '''/**
 * <p>Gets a fraction raised to a positive power.</p>
 *
 * @param fraction  the fraction to raise, not null
 * @param power  the power to raise the fraction to, positive
 * @return the fraction raised to the power
 */
public static Fraction raisedFraction(Fraction fraction, int power) {
    Fraction result = fraction;
    for (int bit = Integer.highestOneBit(power) >>> 1; bit != 0; bit >>>= 1) {
        result = result.multiplyBy(result);
        if ((power & bit) != 0) {
            result = result.multiplyBy(fraction);
        }
    }
    return result;
}'''

HOP1 = '''/**
 * <p>Gets a fraction raised to the passed in power.</p>
 *
 * <p>A power of zero gives <code>Fraction.ONE</code>, even if the
 * fraction equals <code>Fraction.ZERO</code>.</p>
 *
 * @param fraction  the fraction to raise, not null
 * @param power  the power to raise the fraction to
 * @return the fraction raised to the power
 */
public static Fraction fractionToPower(Fraction fraction, int power) {
    if (power == 0) {
        return Fraction.ONE;
    }
    return StringUtils.fractionPower(fraction, power);
}'''

HOP2 = '''/**
 * <p>Gets a fraction raised to a power other than zero.</p>
 *
 * <p>A negative power raises the reciprocal of the fraction to the
 * magnitude of the power. The magnitude of <code>Integer.MIN_VALUE</code>
 * does not fit in an <code>int</code>, so for that power the square of
 * the reciprocal is raised to half the magnitude.</p>
 *
 * @param fraction  the fraction to raise, not null
 * @param power  the power to raise the fraction to, not zero
 * @return the fraction raised to the power
 */
public static Fraction fractionPower(Fraction fraction, int power) {
    if (power > 0) {
        return ArrayUtils.powerOfFraction(fraction, power);
    }
    Fraction reciprocal = fraction.invert();
    if (power == Integer.MIN_VALUE) {
        return ArrayUtils.powerOfFraction(reciprocal.multiplyBy(reciprocal), -(power / 2));
    }
    return ArrayUtils.powerOfFraction(reciprocal, -power);
}'''

HOP3 = '''/**
 * <p>Gets a fraction raised to a positive power.</p>
 *
 * @param fraction  the fraction to raise, not null
 * @param power  the power to raise the fraction to, positive
 * @return the fraction raised to the power
 */
public static Fraction powerOfFraction(Fraction fraction, int power) {
    return StrBuilder.raiseFraction(fraction, power);
}'''

HOP4 = '''/**
 * <p>Gets a fraction raised to a positive power.</p>
 *
 * @param fraction  the fraction to raise, not null
 * @param power  the power to raise the fraction to, positive
 * @return the fraction raised to the power
 */
public static Fraction raiseFraction(Fraction fraction, int power) {
    return FastDateFormat.raisedFraction(fraction, power);
}'''

DESIGN = {
 "instance": "Lang-49", "project": "Lang", "bug_id": 49, "seed": 3696,
 "src_root": "src/java", "test_root": "src/test",
 "facade_variant": "V2",
 "state_passed": "receiver this (as Fraction fraction) and the argument power; no field read or written, no write-back",
 "facade": {"file": FR, "class": FRACTION, "method": "pow", "near_line": 542},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/math/FractionTest.java",
             "test_class": "org.apache.commons.lang.math.FractionTest", "test_method": "testPow"},
 "expected_signature": "expected:<9> but was:<3>",
 "gold": {"method": "raisedFraction", "text": GOLD_TEXT,
          "fault": {"old": "            result = result.multiplyBy(result);\n"
                           "            if ((power & bit) != 0) {",
                    "new": "            if ((power & bit) != 0) {"}},
 "chain": {
   "facade_body": "return org.apache.commons.lang.builder.ToStringStyle.fractionToPower(this, power);",
   "lie": "The numerator and the denominator are each raised to the power on their own, and the two results are then "
          "divided by their greatest common divisor.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "fractionToPower",
      "imports": ["org.apache.commons.lang.StringUtils", FRACTION], "text": HOP1},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "fractionPower",
      "imports": [FRACTION], "text": HOP2},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "powerOfFraction",
      "imports": [FRACTION, "org.apache.commons.lang.text.StrBuilder"], "text": HOP3},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "raiseFraction",
      "imports": [FRACTION, "org.apache.commons.lang.time.FastDateFormat"], "text": HOP4},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "raisedFraction",
      "imports": [FRACTION], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.math.Fraction::multiplyBy",
              "org.apache.commons.lang.math.Fraction::divideBy",
              "org.apache.commons.lang.math.Fraction::invert"],
 "ownership_reason": "Only the gold sees the bits of the power together with the running result: hop 1 decides the zero "
                     "power, hop 2 turns a negative power into the reciprocal raised to the magnitude, and hops 3 and 4 pass "
                     "the fraction and the power along; each gets back one Fraction. Once the gold has returned, no caller can "
                     "tell which products were formed, and no caller can supply the squarings without computing the power "
                     "itself. The gold's javadoc promises the fraction raised to a positive power, which 3/5 raised to 2 "
                     "(9/25) is not when 3/5 comes back. The convention is pinned outside the gold: Fraction.multiplyBy is the "
                     "product the gold is built on, and FractionTest testMultiply multiplies 6/10 by 6/10 to 9/25 and that "
                     "by 6/10 to 27/125 (the square and the cube) and passes; Fraction.divideBy forms a quotient as the "
                     "product with the reciprocal (testDivide), the convention hop 2 uses for a negative power; "
                     "Fraction.invert gives the reciprocal unreduced (testInvert); the facade's javadoc states that the "
                     "result is the fraction raised to the passed in power, in reduced form.",
 "ownership_tests": ["org.apache.commons.lang.math.FractionTest::testMultiply",
                     "org.apache.commons.lang.math.FractionTest::testDivide",
                     "org.apache.commons.lang.math.FractionTest::testInvert"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "return FastDateFormat.raisedFraction(fraction, power);",
      "new": "return (power & 1) == 0 ? FastDateFormat.raisedFraction(fraction.multiplyBy(fraction), power / 2) : FastDateFormat.raisedFraction(fraction, power);",
      "why": "hop 4 squares the fraction and halves an even power before delegating"},
     {"file": AU, "old": "return StrBuilder.raiseFraction(fraction, power);",
      "new": "return StrBuilder.raiseFraction(fraction.reduce(), power);",
      "why": "hop 3 reduces the fraction before delegating"},
     {"file": TSS, "old": "return StringUtils.fractionPower(fraction, power);",
      "new": "return StringUtils.fractionPower(power > 1 ? fraction.multiplyBy(fraction) : fraction, power);",
      "why": "hop 1 squares the fraction for a power above one"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are hosts_hop_order of the task record (bridge7_tasks.json), in that order, none "
               "substituted; they equal the seeded draw for seed 3696 (mr_lib preview, target "
               "org/apache/commons/lang/math/Fraction.java): builder.ToStringStyle (hop 1, 2285 lines), StringUtils (hop 2, "
               "5501), ArrayUtils (hop 3, 4417), text.StrBuilder (hop 4, 2712), time.FastDateFormat (hop 5, gold, 1747; the "
               "smallest host; the pool of five hosts of at least 1500 lines is exhausted at five). All five are public "
               "top-level classes in which a static method compiles (ToStringStyle is abstract, which does not affect a "
               "static method). Anchors (stageB_lib.pick_insertion_anchor via insert_hop, seed 3696 + 100 + i): hop 1 after "
               "`append` (line idx 718, seed 3796), hop 2 after `stripAll` (593, 3797), hop 3 after `remove` (3891, 3798), "
               "hop 4 after `appendln` (835, 3799), hop 5 after `format` (858, 3800); all in the outer class. The facade "
               "calls hop 1 by its fully-qualified name; each hop imports Fraction and the next host (StringUtils and "
               "ArrayUtils share a package).",
}
