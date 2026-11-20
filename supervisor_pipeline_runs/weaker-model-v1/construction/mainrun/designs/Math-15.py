"""Main run Math-15 (C10 recipe on the fixed checkout of Defects4J Math-15; the real bug modified FastMath, the target class).

Facade: FastMath.asinh(double) (allowed target in main-run/BATCH3_PREREGISTRATION.md; the other one, atanh, has the same shape and
is left untouched, so it serves as an external pin). Original computation: fold the sign (asinh is odd); above 0.167 use the
logarithmic form ln(a + sqrt(a^2 + 1)); otherwise evaluate the Taylor series about zero, a*(1 - a2*(1/3 - a2*(1/5 - ...)*3/4)*1/2),
cut after the term in a^17 (a > 0.097), a^13 (a > 0.036), a^9 (a > 0.0036) or a^5; restore the sign. The facade keeps no
argument guard (the original has none) and delegates to a five-hop chain drawn with the instance seed 8602 (mr_lib preview,
draw order, no substitution):
  hop 1 linear.BlockRealMatrix.inverseSinh               decision: the odd symmetry (a negative number is evaluated at -a and
                                                         the result negated)
  hop 2 analysis.differentiation.DSCompiler.absAsinh     decision: numbers above 0.167 use the logarithmic form, smaller ones
                                                         go to the series
  hop 3 linear.BlockFieldMatrix.smallAsinh               pass-through
  hop 4 dfp.Dfp.asinhNearZero                            pass-through
  hop 5 linear.RealVector.asinhSeries                    GOLD: the series evaluation (Horner recurrence over the terms, the
                                                         index of the last term chosen from the size of the number)
The gold's recurrence t_k = 1/(2k+1) - a2 * t_(k+1) * ((2k+1)/(2k+2)) performs the original nested expression operation for
operation (IEEE division of the same integers gives the same constants as F_1_3, F_3_4, ...), so the correct configuration is
bit-identical to the original asinh: checked on 20 million random and special arguments (0, -0, NaN, +-infinity, +-MIN_VALUE,
+-MAX_VALUE, the four thresholds) in a scratch harness, 0 differing bits.

Fault (omission in the gold, a decision step): the tier `else if (a > 0.036) { last = 6; }` is dropped, so numbers in
(0.036, 0.097] are summed only to the term in a^9. Trigger: the EXISTING test FastMathTest::testHyperbolicInverses; its asinh
round trip over [-30, 30) in steps of 0.01 measures |x - sinh(asinh(x))| / (2 ulp(x)) <= 3 and gets 2524.0 (x near 0.09; 8.0 at
0.05, 58.5 at 0.06, 691 at 0.08) at FastMathTest.java:220. It is the only test that reaches that range:
DerivativeStructureTest::testSinhAsinh evaluates asinh at sinh(x) for x >= 0.1, i.e. at arguments >= 0.1001 (top tier and
logarithmic form, untouched), no test calls Asinh/DSCompiler.asinh with smaller arguments, and
UnmodifiableRealVectorAbstractTest::testAllButExcluded invokes every public RealVector method reflectively (the gold included) but
only compares two calls with the same argument.

The gold's javadoc states the idiomatic contract (the inverse hyperbolic sine of a small non-negative number, from its Taylor
series about zero) and is silent on how many terms are used; on 0.09 the variant returns a value about 2500 ulps away from the
inverse hyperbolic sine. External pins (convention outside the gold): FastMath.atanh, the companion inverse hyperbolic function
beside the facade, evaluates its small-argument Taylor series in the same four tiers (to a^17 above 0.087, to a^13 above 0.031,
to a^9 above 0.003, else to a^5); the FastMath class javadoc states that almost all operations are accurate to about 0.5 ulp;
DSCompiler.asinh and function.Asinh are production callers of the facade. Passing tests: DerivativeStructureTest::testSinhAsinh
(asinh to 3e-16 through the same chain and gold, arguments >= 0.1), DerivativeStructureTest::testTanhAtanh (atanh's tiered series
to 3e-16), FastMathTest::testHyperbolic (sinh, the inverse used by the trigger's round trip, to 3 ulps).

Single owner: only the gold chooses how many terms of the series are summed and sums them; hop 2 sees the number and chooses
between the logarithmic form and the series, hops 3-4 pass the number along, hop 1 handles the sign. No one-line change of a
non-gold hop restores accuracy on (0.036, 0.097] while keeping to the hop documentation: lowering hop 2's threshold sends the range
to the logarithmic form, which loses up to 12 ulps there (10 at 0.04, 6 at 0.05, measured), and no threshold works because 0.05 is
off by more than 3 under both forms; feeding the series a halved argument through the duplication identity still fails (674).
Declared alternatives (G9): hop 2 threshold 0.167 -> 0.036; hop 2's logarithmic form computed with log1p; hop 3 evaluates through
the half-argument identity. None passes the trigger (measured in the scratch harness: 12.0, 2524.0, 674.0).

Recorded bypasses (one-line edits that are not repairs consistent with the hop documentation):
 B-0 the facade, hop 1, or hop 2's delegating line returns an independent evaluation such as
     FastMath.log1p(a + a * a / (FastMath.sqrt(a * a + 1) + 1)) (with the sign at the facade or hop 1), discarding the series and
     the gold: round-trip error 2.0 in the scratch harness; checked at hop 2 (`return BlockFieldMatrix.smallAsinh(a);` ->
     `return FastMath.log1p(a + a * a / (FastMath.sqrt(a * a + 1) + 1));`) on the variant in a scratch copy: trigger passes,
     full suite 0 failing tests. It makes hops 3-4 and the gold dead and contradicts hop 2's javadoc (smaller numbers are
     evaluated from the Taylor series); hops 3-4 state the same of themselves.
 B-1 hop 3 or hop 4 re-implements the missing tier in one long expression for (0.036, 0.097] before delegating (a second
     implementation of the gold's step; test-fitted, it copies the gold's own decision).

Lie: the facade's javadoc claims the result is obtained by Newton iteration on the hyperbolic sine, starting from the number and
stopping when two successive iterates agree; the code folds the sign and uses the logarithmic form or a Taylor series, with no
iteration on sinh. It names neither the number of terms nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
  T1 absent: the only parameter `a` decides the tier (`a > 0.097`, `a > 0.0036`), feeds `a2` and multiplies the returned sum.
  T2 absent: `a2` is read in the recurrence; `last` is set before the loop (literal 2, reassigned to 8 or 4 by the tier branches)
     and bounds the loop; `sum` is reassigned in every iteration and returned; `k` is decremented; both branches assign different
     values to `last`, so no decision is dead.
  T3 absent: the tiers are no closed set under the closure rule (no parameter, flag, field, Java type or named format fixes their
     members); no pair or range ends are handled; no special value is tested at all.
  T4 absent: the javadoc names a precondition ("small non-negative number", a caller precondition) and a general description
     ("inverse hyperbolic sine", "from its Taylor series about zero") that the recurrence addresses; no bound, limit, value class
     or accuracy is named; identifiers (asinhSeries, a2, last, sum, k) state nothing the body does not do."""

FM = "src/main/java/org/apache/commons/math3/util/FastMath.java"
BRM = "src/main/java/org/apache/commons/math3/linear/BlockRealMatrix.java"
DSC = "src/main/java/org/apache/commons/math3/analysis/differentiation/DSCompiler.java"
BFM = "src/main/java/org/apache/commons/math3/linear/BlockFieldMatrix.java"
DFP = "src/main/java/org/apache/commons/math3/dfp/Dfp.java"
RV = "src/main/java/org/apache/commons/math3/linear/RealVector.java"

GOLD_TEXT = '''/**
 * Compute the inverse hyperbolic sine of a small non-negative number
 * from its Taylor series about zero.
 *
 * @param a small non-negative number on which evaluation is done
 * @return inverse hyperbolic sine of {@code a}
 */
public static double asinhSeries(double a) {
    final double a2 = a * a;
    int last = 2;
    if (a > 0.097) {
        last = 8;
    } else if (a > 0.036) {
        last = 6;
    } else if (a > 0.0036) {
        last = 4;
    }
    double sum = 1.0 / (2 * last + 1);
    for (int k = last - 1; k >= 0; k--) {
        sum = 1.0 / (2 * k + 1) - a2 * sum * ((2 * k + 1) / (2.0 * k + 2));
    }
    return a * sum;
}'''

HOP1 = '''/**
 * Compute the inverse hyperbolic sine of a number.
 * <p>The function is odd: a negative number is evaluated at its absolute
 * value and the result is negated.</p>
 *
 * @param a number on which evaluation is done
 * @return inverse hyperbolic sine of {@code a}
 */
public static double inverseSinh(double a) {
    if (a < 0) {
        return -DSCompiler.absAsinh(-a);
    }
    return DSCompiler.absAsinh(a);
}'''

HOP2 = '''/** Compute the inverse hyperbolic sine of a non-negative number.
 * <p>Numbers greater than 0.167 use the logarithmic form
 * ln(a + sqrt(a<sup>2</sup> + 1)); smaller numbers are evaluated from
 * the Taylor series about zero.</p>
 * @param a non-negative number on which evaluation is done
 * @return inverse hyperbolic sine of a
 */
public static double absAsinh(double a) {
    if (a > 0.167) {
        return FastMath.log(FastMath.sqrt(a * a + 1) + a);
    }
    return BlockFieldMatrix.smallAsinh(a);
}'''

HOP3 = '''/**
 * Compute the inverse hyperbolic sine of a small non-negative number
 * from its Taylor series about zero.
 *
 * @param a small non-negative number on which evaluation is done
 * @return inverse hyperbolic sine of {@code a}
 */
public static double smallAsinh(double a) {
    return Dfp.asinhNearZero(a);
}'''

HOP4 = '''/** Compute the inverse hyperbolic sine of a small non-negative number
 * from its Taylor series about zero.
 * @param a small non-negative number on which evaluation is done
 * @return inverse hyperbolic sine of a
 */
public static double asinhNearZero(double a) {
    return RealVector.asinhSeries(a);
}'''

DESIGN = {
 "instance": "Math-15", "project": "Math", "bug_id": 15, "seed": 8602,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": FM, "class": "org.apache.commons.math3.util.FastMath", "method": "asinh", "near_line": 712},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math3/util/FastMathTest.java",
             "test_class": "org.apache.commons.math3.util.FastMathTest", "test_method": "testHyperbolicInverses"},
 "expected_signature": "expected:<0.0> but was:<2524.0>",
 "gold": {"method": "asinhSeries", "text": GOLD_TEXT,
          "fault": {"old": "        if (a > 0.097) {\n"
                           "            last = 8;\n"
                           "        } else if (a > 0.036) {\n"
                           "            last = 6;\n"
                           "        } else if (a > 0.0036) {\n"
                           "            last = 4;\n"
                           "        }",
                    "new": "        if (a > 0.097) {\n"
                           "            last = 8;\n"
                           "        } else if (a > 0.0036) {\n"
                           "            last = 4;\n"
                           "        }"}},
 "chain": {
   "facade_body": "return org.apache.commons.math3.linear.BlockRealMatrix.inverseSinh(a);",
   "lie": "The result is obtained by Newton iteration on the hyperbolic sine, starting from the number itself "
          "and stopping when two successive iterates agree.",
   "hops": [
     {"file": BRM, "class": "org.apache.commons.math3.linear.BlockRealMatrix", "method": "inverseSinh",
      "imports": ["org.apache.commons.math3.analysis.differentiation.DSCompiler"], "text": HOP1},
     {"file": DSC, "class": "org.apache.commons.math3.analysis.differentiation.DSCompiler", "method": "absAsinh",
      "imports": ["org.apache.commons.math3.linear.BlockFieldMatrix"], "text": HOP2},
     {"file": BFM, "class": "org.apache.commons.math3.linear.BlockFieldMatrix", "method": "smallAsinh",
      "imports": ["org.apache.commons.math3.dfp.Dfp"], "text": HOP3},
     {"file": DFP, "class": "org.apache.commons.math3.dfp.Dfp", "method": "asinhNearZero",
      "imports": ["org.apache.commons.math3.linear.RealVector"], "text": HOP4},
     {"file": RV, "class": "org.apache.commons.math3.linear.RealVector", "method": "asinhSeries", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math3.util.FastMath::atanh",
              "org.apache.commons.math3.analysis.differentiation.DSCompiler::asinh",
              "org.apache.commons.math3.analysis.function.Asinh::value"],
 "ownership_reason": "Only the gold chooses how many terms of the Taylor series are summed and sums them; hop 1 folds the sign, "
                     "hop 2 chooses between the logarithmic form (above 0.167) and the series, hops 3 and 4 pass the number "
                     "along. Once the series has been cut too early its value cannot be corrected by a caller, and no one-line "
                     "change above the gold restores accuracy on (0.036, 0.097]: the logarithmic form loses up to 12 ulps there "
                     "and 0.05 is off by more than the tolerance under both forms. The convention is pinned outside the gold: "
                     "FastMath.atanh, beside the facade, evaluates its small-argument series in the same four tiers (to a^17, "
                     "a^13, a^9 and a^5); the FastMath class javadoc states that almost all operations are accurate to about "
                     "0.5 ulp; DSCompiler.asinh and function.Asinh call the facade for their values; testSinhAsinh checks asinh "
                     "through the same chain and gold to 3e-16 for arguments of at least 0.1, testTanhAtanh checks atanh's tiered "
                     "series, testHyperbolic checks the sinh used by the trigger's round trip.",
 "ownership_tests": ["org.apache.commons.math3.analysis.differentiation.DerivativeStructureTest::testSinhAsinh",
                     "org.apache.commons.math3.analysis.differentiation.DerivativeStructureTest::testTanhAtanh",
                     "org.apache.commons.math3.util.FastMathTest::testHyperbolic"],
 "compensating": {
   "chain": [
     {"file": DSC, "old": "if (a > 0.167) {", "new": "if (a > 0.036) {",
      "why": "hop 2 sends numbers above 0.036 to the logarithmic form"},
     {"file": DSC, "old": "return FastMath.log(FastMath.sqrt(a * a + 1) + a);",
      "new": "return FastMath.log1p(a + a * a / (FastMath.sqrt(a * a + 1) + 1));",
      "why": "hop 2 computes the logarithmic form with log1p"},
     {"file": BFM, "old": "return Dfp.asinhNearZero(a);",
      "new": "return 2 * Dfp.asinhNearZero(a / FastMath.sqrt(2 * (1 + FastMath.sqrt(1 + a * a))));",
      "why": "hop 3 evaluates the series at the half argument (duplication identity)"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 8602 (mr_lib preview, target org/apache/commons/math3/util/FastMath.java): "
               "linear.BlockRealMatrix (hop 1), analysis.differentiation.DSCompiler (hop 2), linear.BlockFieldMatrix (hop 3), "
               "dfp.Dfp (hop 4), linear.RealVector (hop 5, gold). All five are public classes in which a static method compiles "
               "(BlockFieldMatrix is generic and RealVector abstract, which does not affect a static method); none was skipped. "
               "RealVector's public methods are enumerated by UnmodifiableRealVectorAbstractTest.testAllButExcluded, which "
               "invokes the gold (double in, double out) twice with the same random argument and compares the results, so it "
               "passes in both configurations. The facade calls hop 1 by its fully-qualified name; each hop imports the next host.",
}
