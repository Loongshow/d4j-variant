"""Main run Lang-49 (C10 recipe on the fixed checkout of Defects4J Lang-49; the real bug modified math.Fraction, the target class).

Facade: Fraction.getReducedFraction(int, int), the only allowed target for this instance (BATCH3_PREREGISTRATION.md, pool rank 7).
Original computation: reject a zero denominator; a zero numerator gives ZERO; halve both parts when the denominator is
Integer.MIN_VALUE and the numerator is even; move a negative sign to the numerator (throwing when a part cannot be negated);
divide both parts by their greatest common divisor (the private binary gcd); construct the fraction.

Chain (hosts in draw order for the instance seed 3696, mr_lib preview, target org/apache/commons/lang/math/Fraction.java):
  hop 1 builder.ToStringStyle.simplestFraction   decision: a zero numerator gives Fraction.ZERO, else delegates
  hop 2 StringUtils.fractionOfParts              pass-through
  hop 3 ArrayUtils.partsAsFraction               pass-through
  hop 4 text.StrBuilder.fractionFromParts        pass-through
  hop 5 time.FastDateFormat.lowestTerms          GOLD: the reduction core. In long arithmetic it moves a negative sign to the
                                                 numerator (both parts negated), runs Euclid's algorithm on the remainders
                                                 (each remainder taken as a magnitude, loop while the second operand is
                                                 positive), and builds Fraction.getFraction(numerator / gcd, denominator / gcd)
                                                 from the ORIGINAL signed parts, so getFraction(int, int) resolves the sign and
                                                 throws when a part cannot be negated.
The facade keeps its argument guard (zero denominator -> ArithmeticException) and delegates to hop 1. Fraction's constructor and
gcd are private, so the gold computes its own gcd and builds the result through the public getFraction(int, int). Working in
long arithmetic, the gold needs no Integer.MIN_VALUE halving: (-2, MIN) has gcd 2 and gives getFraction(-1, -2^30) = 1/2^30;
(-7, MIN) has gcd 1 and getFraction(-7, MIN) throws, exactly as before. The correct configuration equals the original on every
input the suite passes (simulated over all 199,275 recorded calls of the full suite) and is value-equal or more exact on untested
corners (MIN, even): the original left (MIN, 2) unreduced and threw for (MIN, -2); the chain gives -2^30/1 and 2^30/1.

Fault (omission of one step in the gold): the sign-normalisation block `if (v < 0) { u = -u; v = -v; }` is dropped. With a
negative denominator the Euclid loop (`while (v > 0)`) never runs, the divisor is the numerator itself, and the parts are
truncated: (6, -10) gives getFraction(1, -1) = -1/1. Positive denominators are unaffected (the block never runs for them).
Trigger: the EXISTING test FractionTest::testReducedFactory_int_int; (0,1) ... (-6, 10) pass, then
getReducedFraction(6, -10) expects numerator -3 and gets -1 ("expected:<-3> but was:<-1>"). It is the only test in the suite
that passes a negative denominator to getReducedFraction (recorded over the full suite: getFraction(double) and multiplyBy /
divideBy / pow always pass a positive denominator), so G5 holds.

The gold's javadoc states the idiomatic contract (a fraction from a numerator and a non-zero denominator, in lowest terms) and is
silent on signs. The convention is pinned outside the gold: the facade's own javadoc ("Any negative signs are resolved to be on
the numerator"); Fraction.getFraction(int, int) negates both parts when the denominator is negative (testFactory_int_int:
(6, -10) -> -6/10, (-6, -10) -> 6/10); Fraction.invert() resolves the sign onto the numerator (testInvert: -15/47 -> -47/15);
Fraction.reduce() takes the gcd of the numerator's magnitude (testReduce: 2/-3 -> -2/3).

Single owner. Hops 1-4 hold only the two int parts; the trigger's MIN cases make every one-line sign repair above the gold fail,
because negating Integer.MIN_VALUE in int arithmetic overflows while the gold works in long arithmetic:
  - sign normalisation at a hop (negate both when the denominator is negative): (-2, MIN) becomes (2, MIN), value -1/2^30
    instead of 1/2^30; with a MIN guard, (-7, MIN) reaches the gold unnormalised and gives 1/306783378 instead of throwing;
  - magnitude of the denominator plus negate(): same two failures;
  - .reduce() (or any re-reduction) on the gold's result: (6, -10) already has the value -1, which no reduction recovers;
  - building Fraction.getFraction(n, d) first (then the gold on its parts, or .reduce() on it): getFraction(-2, MIN) throws;
  - swapping the parts and inverting the result: (-6, -10) or (-2, MIN) build a zero denominator or the wrong value;
  - halving both parts (when both are even, or the original MIN-only halving): (6, -10) -> (3, -5) is still truncated to -1/1.
All of these were simulated on the variant over the trigger and the recorded inputs of the rest of the suite; none passes the
trigger. Declared alternatives (G9): hop 4 moves the sign to the numerator before delegating; hop 3 calls reduce() on the result;
hop 2 passes the magnitude of a negative denominator and negates the result. No one-line bypass that discards the gold was found
either (getFraction(n, d).reduce() throws on (-2, MIN); getFraction((double) n / d) gives 0/1 for (-2, MIN)); the only bypass is
restoring the original multi-statement body (halving, sign step with overflow checks, gcd) in the facade or a hop.

Lie: the facade's javadoc gains the claim that common factors are cast out one prime at a time (both parts divided by two while
both are even, then by each larger prime in turn); the chain uses Euclid's remainders and never divides by primes. It names
neither signs nor any hop nor the omitted step.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), whole gold:
  VARIANT gold (as the checker sees it):
  T1 absent: numerator is read in `long u = numerator` (the divisor) and in the return; denominator in `long v = denominator`
     (loop bound and operand) and in the return; no parameter is used only in an argument check.
  T2 absent: u, v and t are all assigned inside the loop and reach the return (u is the divisor); nothing is initialised to a
     literal; there is no if/else, switch or ternary, so no dead decision.
  T3 absent: the two parts (numerator, denominator) are both divided by the divisor; no member of any closed set gets a sign,
     zero or special-value treatment (no member handled); Math.abs applies to every remainder alike; the text names no class.
  T4 absent: "in lowest terms" is a general description of the result; "not zero" is a caller precondition; no identifier or
     comment names a rule, bound or value class.
  CORRECT gold: T1 absent (same reads); T2 absent (`if (v < 0)` negates both live locals and decides whether the loop runs; u, v,
  t move in the loop); T3 absent (the sign block negates both parts together; both parts are divided); T4 absent (same text).
"""

FR = "src/java/org/apache/commons/lang/math/Fraction.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
SU = "src/java/org/apache/commons/lang/StringUtils.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
FRACTION = "org.apache.commons.lang.math.Fraction"

GOLD_TEXT = '''/**
 * <p>Creates a <code>Fraction</code> from a numerator and a denominator,
 * in lowest terms.</p>
 *
 * @param numerator  the numerator
 * @param denominator  the denominator, not zero
 * @return a new fraction instance in lowest terms
 */
public static Fraction lowestTerms(int numerator, int denominator) {
    long u = numerator;
    long v = denominator;
    if (v < 0) {
        u = -u;
        v = -v;
    }
    while (v > 0) {
        long t = Math.abs(u % v);
        u = v;
        v = t;
    }
    return Fraction.getFraction((int) (numerator / u), (int) (denominator / u));
}'''

HOP1 = '''/**
 * <p>Creates a <code>Fraction</code> from a numerator and a denominator,
 * in lowest terms.</p>
 *
 * <p>A zero numerator gives <code>Fraction.ZERO</code>.</p>
 *
 * @param numerator  the numerator
 * @param denominator  the denominator, not zero
 * @return a fraction instance in lowest terms
 */
public static Fraction simplestFraction(int numerator, int denominator) {
    if (numerator == 0) {
        return Fraction.ZERO;
    }
    return StringUtils.fractionOfParts(numerator, denominator);
}'''

PASS_DOC = '''/**
 * <p>Creates a <code>Fraction</code> from a non-zero numerator and a
 * denominator, in lowest terms.</p>
 *
 * @param numerator  the numerator, not zero
 * @param denominator  the denominator, not zero
 * @return a new fraction instance in lowest terms
 */'''

HOP2 = PASS_DOC + '''
public static Fraction fractionOfParts(int numerator, int denominator) {
    return ArrayUtils.partsAsFraction(numerator, denominator);
}'''

HOP3 = PASS_DOC + '''
public static Fraction partsAsFraction(int numerator, int denominator) {
    return StrBuilder.fractionFromParts(numerator, denominator);
}'''

HOP4 = PASS_DOC + '''
public static Fraction fractionFromParts(int numerator, int denominator) {
    return FastDateFormat.lowestTerms(numerator, denominator);
}'''

DESIGN = {
 "instance": "Lang-49", "project": "Lang", "bug_id": 49, "seed": 3696,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": FR, "class": FRACTION, "method": "getReducedFraction", "near_line": 209},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/math/FractionTest.java",
             "test_class": "org.apache.commons.lang.math.FractionTest", "test_method": "testReducedFactory_int_int"},
 "expected_signature": "expected:<-3> but was:<-1>",
 "gold": {"method": "lowestTerms", "text": GOLD_TEXT,
          "fault": {"old": "        long v = denominator;\n"
                           "        if (v < 0) {\n"
                           "            u = -u;\n"
                           "            v = -v;\n"
                           "        }\n"
                           "        while (v > 0) {",
                    "new": "        long v = denominator;\n"
                           "        while (v > 0) {"}},
 "chain": {
   "facade_body": "if (denominator == 0) {\n            throw new ArithmeticException(\"The denominator must not be zero\");\n        }\n"
                  "        return org.apache.commons.lang.builder.ToStringStyle.simplestFraction(numerator, denominator);",
   "lie": "The common factors are cast out one prime at a time, both parts being divided by two for as long as both are "
          "even and then by each larger prime in turn.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "simplestFraction",
      "imports": [FRACTION, "org.apache.commons.lang.StringUtils"], "text": HOP1},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "fractionOfParts",
      "imports": [FRACTION], "text": HOP2},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "partsAsFraction",
      "imports": [FRACTION, "org.apache.commons.lang.text.StrBuilder"], "text": HOP3},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "fractionFromParts",
      "imports": [FRACTION, "org.apache.commons.lang.time.FastDateFormat"], "text": HOP4},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "lowestTerms",
      "imports": [FRACTION], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.math.Fraction::getFraction",
              "org.apache.commons.lang.math.Fraction::invert",
              "org.apache.commons.lang.math.Fraction::reduce"],
 "ownership_reason": "Only the gold works on the two parts arithmetically: hop 1 returns ZERO for a zero numerator and hops 2-4 "
                     "pass the two int parts along. The gold must move a negative sign to the numerator before its Euclid loop, "
                     "which runs only while the second operand is positive; without that step a negative denominator skips the "
                     "loop and the parts are truncated by the numerator itself (6/-10 becomes -1/1), a wrong value that no later "
                     "reduction recovers. The step cannot be moved above the gold in one line: the hops hold int parts, so "
                     "negating a part equal to Integer.MIN_VALUE overflows, and the trigger's cases (-2, MIN) -> 1/2^30 and "
                     "(-7, MIN) -> ArithmeticException then fail (normalising at a hop, with or without a MIN guard, or passing "
                     "the denominator's magnitude and negating, or building getFraction(n, d) first, all fail one of them). The "
                     "convention is pinned outside the gold: the facade's javadoc ('Any negative signs are resolved to be on the "
                     "numerator'); Fraction.getFraction(int, int) negates both parts for a negative denominator "
                     "(testFactory_int_int: 6/-10 -> -6/10, -6/-10 -> 6/10); Fraction.invert() resolves the sign onto the "
                     "numerator (testInvert); Fraction.reduce() takes the gcd of the numerator's magnitude (testReduce: 2/-3 -> "
                     "-2/3). The gold's javadoc accepts any non-zero denominator and promises the fraction in lowest terms, "
                     "which -1/1 for 6/-10 is not.",
 "ownership_tests": ["org.apache.commons.lang.math.FractionTest::testFactory_int_int",
                     "org.apache.commons.lang.math.FractionTest::testInvert",
                     "org.apache.commons.lang.math.FractionTest::testReduce",
                     "org.apache.commons.lang.math.FractionTest::testMultiply",
                     "org.apache.commons.lang.math.FractionTest::testFactory_double"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "return FastDateFormat.lowestTerms(numerator, denominator);",
      "new": "return denominator < 0 ? FastDateFormat.lowestTerms(-numerator, -denominator) : FastDateFormat.lowestTerms(numerator, denominator);",
      "why": "hop 4 moves a negative sign to the numerator before delegating"},
     {"file": AU, "old": "return StrBuilder.fractionFromParts(numerator, denominator);",
      "new": "return StrBuilder.fractionFromParts(numerator, denominator).reduce();",
      "why": "hop 3 reduces the fraction it receives once more"},
     {"file": SU, "old": "return ArrayUtils.partsAsFraction(numerator, denominator);",
      "new": "return denominator < 0 ? ArrayUtils.partsAsFraction(numerator, -denominator).negate() : ArrayUtils.partsAsFraction(numerator, denominator);",
      "why": "hop 2 passes the magnitude of a negative denominator and negates the result"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 3696 (mr_lib preview, target org/apache/commons/lang/math/Fraction.java; the host "
               "pool has exactly these five files): builder.ToStringStyle (hop 1), StringUtils (hop 2), ArrayUtils (hop 3), "
               "text.StrBuilder (hop 4), time.FastDateFormat (hop 5, gold). All five are public top-level classes in which a "
               "static method compiles (ToStringStyle is abstract, which does not affect a static method) and every anchor is a "
               "top-level method; none was skipped. Each hop imports math.Fraction and the next host (StringUtils -> ArrayUtils "
               "is the same package); the facade calls hop 1 by its fully-qualified name.",
}
