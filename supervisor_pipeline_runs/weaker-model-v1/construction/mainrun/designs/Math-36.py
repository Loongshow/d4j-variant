"""Main run Math-36 (C10 recipe on the fixed checkout of Defects4J Math-36; the real bug modified BigFraction, the target class).

Facade: BigFraction.getReducedFraction(int, int) (the only allowed target, BATCH4_PREREGISTRATION.md row Math-36). It has no
production caller; its only test caller is BigFractionTest::testGetReducedFraction.
Original computation: a zero numerator gives the ZERO constant ("normalize zero"); otherwise new BigFraction(numerator,
denominator), i.e. ZeroException for a zero denominator, division of both parts by their greatest common divisor, and the sign
moved to the numerator.

Why the gold is the common divisor and not a sign or overflow step: every BigFraction built from two parts is normalised by its
constructor, so an omitted sign move or reduction step in a chain that ends in that constructor has no observable effect, and an
input-level special case (the 2^k / -2^31 halving, the zero-denominator check, the sign of a negative fraction) can be
pre-applied by the facade or any hop in one line on the int pair, or recovered from the inputs (the sign). The only part of the
computation whose omission changes the value and that no caller can pre-filter or recover is the common divisor itself: a
divisor that does not divide both parts truncates them, and the lost value cannot be recovered without computing the divisor
elsewhere (a bypass).

The facade keeps its argument guard (zero numerator -> ZERO) and delegates to a five-hop chain drawn with the instance seed
2706 (mr_lib preview, draw order, no substitution):
  hop 1 linear.BlockRealMatrix.fractionFromParts     pass-through (the int parts arrive widened to long)
  hop 2 util.FastMath.normalizedFraction              placement: moves the sign to the numerator
  hop 3 linear.BlockFieldMatrix.exactQuotient         pass-through
  hop 4 dfp.Dfp.lowestTerms                           aggregation: divides both parts by the divisor the gold returns and
                                                      builds the BigFraction
  hop 5 optimization.direct.BOBYQAOptimizer.greatestCommonDivisor
                                                      GOLD: the binary greatest common divisor of the two parts (the same
                                                      algorithm as ArithmeticUtils.gcd(long, long): both parts kept negative,
                                                      common factors of two cast out and counted, then the halving
                                                      difference loop that casts the factors of two out of t)
The correct configuration computes exactly the original result for every int input: the same zero-numerator guard; the sign
move in long arithmetic (no overflow for int parts); the gcd is exact for every pair of int parts (checked against
math.gcd on 20,000 random int pairs and on every pair in [-40, 40]^2 in a scratch simulation); the divisions are exact; the
BigFraction(long, long) constructor then gives the same value; a zero denominator reaches that constructor as (+-1, 0) and
throws the same ZeroException (ZERO_DENOMINATOR) as the original.

Fault (one-line omission of a step inside the gold's iteration): the inner loop that casts the factors of two out of t at the
top of each pass is dropped. t = (v - u) / 2 then halves an odd difference, and the routine returns a number that is not a
common divisor: 6 for (6, 8), 3 for (3, 4), 4 for (8, 6). Trigger: the EXISTING test BigFractionTest::testGetReducedFraction;
its first assertion, assertTrue(new BigFraction(3, 4).equals(BigFraction.getReducedFraction(6, 8))) at line 572, fails
(java.lang.AssertionError): hop 4 divides 6 and 8 by 6 and builds 1 / 1. No other test reaches the chain. The gold's javadoc
states the idiomatic contract (the greatest common divisor of the absolute values of two numbers) and is silent on factors of
two; gcd(6, 8) = 2, so the variant violates that contract on the trigger input.

External pins (convention outside the gold): ArithmeticUtils.gcd(int, int) and ArithmeticUtils.gcd(long, long) run the same
algorithm and cast the factors of two out of t in every pass ('B4/B3: cast out twos from t'), pinned by ArithmeticUtilsTest
testGcd, testGcdLong and testGcdConsistency; Fraction.getReducedFraction reduces both parts by ArithmeticUtils.gcd before
building the fraction (FractionTest::testGetReducedFraction asserts getReducedFraction(6, 8) equals 3/4); ArithmeticUtils.lcm
divides by the same gcd (testLcm).

Single owner: only the gold computes the divisor; hop 4 divides by whatever it returns, hops 1-3 and the facade pass the parts
along (hop 2 moves the sign). The variant's divisor is wrong on reduced inputs too (3 for (3, 4)), so no value-preserving change
of the parts above the gold (pre-reduction, absolute values, swapped order, sign move) makes it divide both parts, and once both
parts have been truncated the fraction cannot be recovered from the result. Declared alternatives (G9): hop 4 takes the divisor
of the parts in the other order (4 for (8, 6): 1 / 2); hop 4 takes the divisor of the absolute values (still 6: 1 / 1); hop 3
reduces the result again (1 / 1 stays 1 / 1).
Recorded one-line edits above the gold that pass the trigger (not repairs of the chain):
 B-0 bypass: the facade (its original body) or any of hops 1-3 returns new BigFraction(numerator, denominator), discarding the
     rest of the chain including the gold.
 B-1 bypass: hop 4 takes its divisor from ArithmeticUtils.gcd(numerator, denominator) instead of the gold.
 B-2 bypass: hop 4 builds new BigFraction(numerator, denominator) without dividing (the constructor reduces), so the gold's
     result is computed and dropped.
 B-3 bypass: hop 4 divides only when the divisor divides both parts and otherwise builds the fraction from the undivided parts;
     on the trigger input the gold's result is discarded.
 T-1 test-fitted identity rewrites: hop 4 calls the gold with (denominator % numerator, numerator) or (numerator, denominator -
     numerator) (the same gcd in exact arithmetic). With the omitted loop they happen to give a common divisor on the five
     trigger inputs (checked on the variant in a scratch copy: trigger passes), but the chain stays wrong on about half of all
     small pairs (scratch simulation): with the first, getReducedFraction(4, 3) returns 1 and (7, 4) returns 3/2; with the
     second, getReducedFraction(3, 1) throws ZeroException and (4, 3) returns 2. They do not repair the computation, they
     break the facade's documented result on ordinary inputs that Fraction.getReducedFraction (evidence) handles, and the gold
     still violates its contract (gcd(3, 4) = 3).
 B-0 to B-3 were each checked on the variant in a scratch copy: the trigger passes.

Lie: the facade's javadoc claims the fraction is obtained by expanding numerator / denominator into a continued fraction and
evaluating its last convergent; no continued fraction or convergent is computed anywhere on the path. It names neither the
divisor, factors of two, the omitted step nor any hop.

No pre-edit is needed: every host already has an import statement, and the gold uses only java.lang.Math.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: p and q initialise u and v, which feed the zero test, the sign normalisation, the common-twos loop, t and the
     returned value.
  T2 absent: u, v, k and t are all read on the way to the return; k is assigned in its loop; t, u and v are assigned in the
     do loop; no literal-initialised local is left unassigned; the zero test, both sign tests, the ternary, the inner while,
     and the if/else in the do loop each have distinct live effects.
  T3 absent: the parameter pair is treated symmetrically everywhere (both zero-tested, both made non-positive, both halved
     together); no closed set has an untreated member.
  T4 absent: the javadoc names only the greatest common divisor of the absolute values; no rule, limit, bound or value class;
     no inline comment.
 Variant gold (the same text without the inner `while ((t & 1) == 0) { t /= 2; }`):
  T1 absent: p and q still initialise u and v, which reach the zero test, the sign normalisation, the common-twos loop, t and
     the return value; neither is only argument-checked.
  T2 absent: u, v, k and t are each read on the way to the return; k is advanced in its loop (k++); in the do loop t is
     reassigned (t = (v - u) / 2) and u or v is assigned on each pass; no literal-initialised local stays unassigned; the zero
     test, the two sign tests, the ternary and the if/else each change the result.
  T3 absent: the closed sets in the gold's text are the parameter pair (p, q) and its copies (u, v): both are zero-tested,
     both negated when positive, both halved together; t is a local, not a member of a closed set; no class, format or
     standard is named; no pair half or range end is treated alone.
  T4 absent: 'the greatest common divisor of the absolute values of two numbers' and '@return the greatest common divisor of
     the absolute values of p and q' are general descriptions that the body's lines address (sign normalisation, abs in the
     zero case, the divisor loop); '@param p first number' and '@param q second number' name nothing; there is no inline
     comment, and the identifiers (u, v, k, t) name no rule or bound."""

BF = "src/main/java/org/apache/commons/math/fraction/BigFraction.java"
BRM = "src/main/java/org/apache/commons/math/linear/BlockRealMatrix.java"
FM = "src/main/java/org/apache/commons/math/util/FastMath.java"
BFM = "src/main/java/org/apache/commons/math/linear/BlockFieldMatrix.java"
DFP = "src/main/java/org/apache/commons/math/dfp/Dfp.java"
BOB = "src/main/java/org/apache/commons/math/optimization/direct/BOBYQAOptimizer.java"
BIGF = "org.apache.commons.math.fraction.BigFraction"

GOLD_TEXT = '''/**
 * Computes the greatest common divisor of the absolute values of two
 * numbers.
 *
 * @param p first number
 * @param q second number
 * @return the greatest common divisor of the absolute values of p and q
 */
public static long greatestCommonDivisor(final long p, final long q) {
    long u = p;
    long v = q;
    if (u == 0 || v == 0) {
        return Math.abs(u) + Math.abs(v);
    }
    if (u > 0) {
        u = -u;
    }
    if (v > 0) {
        v = -v;
    }
    int k = 0;
    while ((u & 1) == 0 && (v & 1) == 0) {
        u /= 2;
        v /= 2;
        k++;
    }
    long t = ((u & 1) == 1) ? v : -(u / 2);
    do {
        while ((t & 1) == 0) {
            t /= 2;
        }
        if (t > 0) {
            u = -t;
        } else {
            v = t;
        }
        t = (v - u) / 2;
    } while (t != 0);
    return -u * (1L << k);
}'''

HOP1 = '''/**
 * Creates a fraction from its numerator and denominator, in lowest terms.
 *
 * @param numerator the numerator
 * @param denominator the denominator
 * @return the fraction numerator / denominator, in lowest terms
 */
public static BigFraction fractionFromParts(final long numerator, final long denominator) {
    return FastMath.normalizedFraction(numerator, denominator);
}'''

HOP2 = '''/**
 * Creates a fraction from its numerator and denominator, in lowest terms.
 * A negative denominator is first made positive by changing the sign of
 * both parts, so that the sign is carried by the numerator.
 *
 * @param numerator the numerator
 * @param denominator the denominator
 * @return the fraction numerator / denominator, in lowest terms
 */
public static BigFraction normalizedFraction(final long numerator, final long denominator) {
    if (denominator < 0) {
        return BlockFieldMatrix.exactQuotient(-numerator, -denominator);
    }
    return BlockFieldMatrix.exactQuotient(numerator, denominator);
}'''

HOP3 = '''/**
 * Creates a fraction from its numerator and a non-negative denominator,
 * in lowest terms.
 *
 * @param numerator the numerator
 * @param denominator the denominator, not negative
 * @return the fraction numerator / denominator, in lowest terms
 */
public static BigFraction exactQuotient(final long numerator, final long denominator) {
    return Dfp.lowestTerms(numerator, denominator);
}'''

HOP4 = '''/**
 * Creates a fraction from its numerator and denominator, in lowest terms:
 * both parts are divided by their greatest common divisor.
 *
 * @param numerator the numerator
 * @param denominator the denominator
 * @return the fraction numerator / denominator, in lowest terms
 */
public static BigFraction lowestTerms(final long numerator, final long denominator) {
    final long divisor = BOBYQAOptimizer.greatestCommonDivisor(numerator, denominator);
    return new BigFraction(numerator / divisor, denominator / divisor);
}'''

DESIGN = {
 "instance": "Math-36", "project": "Math", "bug_id": 36, "seed": 2706,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": BF, "class": BIGF, "method": "getReducedFraction", "near_line": 430},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math/fraction/BigFractionTest.java",
             "test_class": "org.apache.commons.math.fraction.BigFractionTest", "test_method": "testGetReducedFraction"},
 "expected_signature": "testGetReducedFraction(BigFractionTest.java:572)",
 "gold": {"method": "greatestCommonDivisor", "text": GOLD_TEXT,
          "fault": {"old": "        long t = ((u & 1) == 1) ? v : -(u / 2);\n"
                           "        do {\n"
                           "            while ((t & 1) == 0) {\n"
                           "                t /= 2;\n"
                           "            }\n"
                           "            if (t > 0) {",
                    "new": "        long t = ((u & 1) == 1) ? v : -(u / 2);\n"
                           "        do {\n"
                           "            if (t > 0) {"}},
 "chain": {
   "facade_body": "if (numerator == 0) {\n"
                  "            return ZERO; // normalize zero.\n"
                  "        }\n"
                  "        return org.apache.commons.math.linear.BlockRealMatrix.fractionFromParts(numerator, denominator);",
   "lie": "The fraction is obtained by expanding numerator / denominator into a continued fraction and evaluating its "
          "last convergent, which is always in lowest terms.",
   "hops": [
     {"file": BRM, "class": "org.apache.commons.math.linear.BlockRealMatrix", "method": "fractionFromParts",
      "imports": [BIGF], "text": HOP1},
     {"file": FM, "class": "org.apache.commons.math.util.FastMath", "method": "normalizedFraction",
      "imports": [BIGF, "org.apache.commons.math.linear.BlockFieldMatrix"], "text": HOP2},
     {"file": BFM, "class": "org.apache.commons.math.linear.BlockFieldMatrix", "method": "exactQuotient",
      "imports": [BIGF, "org.apache.commons.math.dfp.Dfp"], "text": HOP3},
     {"file": DFP, "class": "org.apache.commons.math.dfp.Dfp", "method": "lowestTerms",
      "imports": [BIGF, "org.apache.commons.math.optimization.direct.BOBYQAOptimizer"], "text": HOP4},
     {"file": BOB, "class": "org.apache.commons.math.optimization.direct.BOBYQAOptimizer", "method": "greatestCommonDivisor",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.util.ArithmeticUtils::gcd",
              "org.apache.commons.math.fraction.Fraction::getReducedFraction",
              "org.apache.commons.math.util.ArithmeticUtils::lcm"],
 "ownership_reason": "Only the gold computes the common divisor of the two parts; hop 4 divides both parts by whatever it "
                     "returns and builds the fraction, hop 2 moves the sign to the numerator, hops 1 and 3 and the facade pass "
                     "the parts along. With the factors of two left in t, t = (v - u) / 2 halves odd differences and the "
                     "routine returns a number that does not divide both parts (6 for (6, 8), 3 for (3, 4)); hop 4's exact "
                     "divisions then truncate, and the value cannot be recovered from the result. The divisor is wrong on "
                     "reduced inputs too, so no value-preserving change of the parts above the gold (pre-reduction, absolute "
                     "values, swapped order, sign move) repairs it; only replacing the gold's result (ArithmeticUtils.gcd, or "
                     "building the fraction from the undivided parts) passes the trigger, which discards the gold. The "
                     "convention is pinned outside the gold: ArithmeticUtils.gcd(int, int) and gcd(long, long) run the same "
                     "binary algorithm and cast the factors of two out of t in every pass (ArithmeticUtilsTest testGcd, "
                     "testGcdLong, testGcdConsistency); Fraction.getReducedFraction reduces both parts by that gcd before "
                     "building the fraction, and FractionTest testGetReducedFraction asserts getReducedFraction(6, 8) equals "
                     "3/4; ArithmeticUtils.lcm divides by the same gcd (testLcm).",
 "ownership_tests": ["org.apache.commons.math.util.ArithmeticUtilsTest::testGcd",
                     "org.apache.commons.math.util.ArithmeticUtilsTest::testGcdLong",
                     "org.apache.commons.math.util.ArithmeticUtilsTest::testGcdConsistency",
                     "org.apache.commons.math.fraction.FractionTest::testGetReducedFraction"],
 "compensating": {
   "chain": [
     {"file": DFP, "old": "BOBYQAOptimizer.greatestCommonDivisor(numerator, denominator);",
      "new": "BOBYQAOptimizer.greatestCommonDivisor(denominator, numerator);",
      "why": "hop 4 takes the divisor of the parts in the other order"},
     {"file": DFP, "old": "BOBYQAOptimizer.greatestCommonDivisor(numerator, denominator);",
      "new": "BOBYQAOptimizer.greatestCommonDivisor(Math.abs(numerator), Math.abs(denominator));",
      "why": "hop 4 takes the divisor of the absolute values of the parts"},
     {"file": BFM, "old": "return Dfp.lowestTerms(numerator, denominator);",
      "new": "return Dfp.lowestTerms(numerator, denominator).reduce();",
      "why": "hop 3 reduces the fraction it gets back once more"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2706 (mr_lib preview, target org/apache/commons/math/fraction/BigFraction.java): "
               "linear.BlockRealMatrix (hop 1), util.FastMath (hop 2), linear.BlockFieldMatrix (hop 3), dfp.Dfp (hop 4), "
               "optimization.direct.BOBYQAOptimizer (hop 5, gold; drawn as the last remaining host: the pool has five usable "
               "classes, FastMathLiteralArrays being unusable). All five are public concrete top-level classes in which a "
               "static method compiles (BlockFieldMatrix is generic, which does not affect a static method); every preview "
               "anchor lies in the outer class; none was skipped. The facade calls hop 1 by its fully-qualified name; each "
               "hop imports BigFraction and the next host (hop 1 already imports FastMath); the gold uses only "
               "java.lang.Math, as the rest of BOBYQAOptimizer does.",
}
