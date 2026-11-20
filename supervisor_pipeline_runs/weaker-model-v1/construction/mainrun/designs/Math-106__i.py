"""Main run Math-106__i (cell C10i, batch 9 / sub-batch 9b: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of
Defects4J Math-106; the real bug modified fraction.ProperFractionFormat, the facade's class). No static pair (pool v2:
no_tested_static; BUILD_BRIEF_C10I_B8_NOTE section 1).

Facade: ProperFractionFormat.format(Fraction, StringBuffer, FieldPosition) (instance method; the only allowed candidate of the task
record, facade_planned_by null, no facade reuse; BATCH9_PREREGISTRATION.md rank 381). It is reached in production through the
inherited Format.format(Object) -> FractionFormat.format(Object, StringBuffer, FieldPosition), which dispatches to it for a
ProperFractionFormat (FractionFormat.getProperInstance).
Original computation: the alignment field is reset (begin and end index 0); num and den are read from the fraction; whole = num / den
and num = num % den; if whole != 0 the whole part is written with getWholeFormat(), then a space, and num becomes Math.abs(num); the
numerator is written with getNumeratorFormat(), then " / ", then the denominator with getDenominatorFormat(); toAppendTo is returned.

facade_variant: V1 (state as parameters). The computation reads three pieces of object state, the whole, numerator and denominator
NumberFormats (the private field wholeFormat of ProperFractionFormat and the private fields numeratorFormat / denominatorFormat of
FractionFormat); the facade reads them through the class's own public getters getWholeFormat(), getNumeratorFormat() and
getDenominatorFormat() (as the original does, so an override of a getter still applies) and passes the three values, with the three
parameters, to hop 1. No field is written, no write-back. The receiver itself is not needed by the chain (only the three formats), so
V2 is not used; no private method is called (no V4); no package-private type is involved (no V3/V5). The facade body is one call to
hop 1 (the original has no argument guard). No visibility is widened, no type is added, no signature, modifier, override or throws
clause changes, no reflection, no test edit.
state_passed: getWholeFormat(), getNumeratorFormat(), getDenominatorFormat() (NumberFormat values) plus the parameters fraction,
toAppendTo and pos, handed to hop 1; no write-back.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-Math-106-probe of the fixture, the first statement of
format(Fraction, StringBuffer, FieldPosition) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j
compile OK; `defects4j test -t org.apache.commons.math.fraction.FractionFormatTest::<m>` for m = testFormat, testFormatNegative,
testFormatZero, testFormatImproper, testFormatImproperNegative: each 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
ProperFractionFormat.format(ProperFractionFormat.java:88), called from FractionFormat.format(FractionFormat.java:202) (Format.format(Object)
from the test's properFormat.format(c)). The facade is reached by five existing tests.

Hosts (host_mode = "largest5"; hosts_hop_order of batch9_tasks.json, used exactly in that order, none substituted):
  hop 1 linear.BigMatrixImpl          1318 lines  formatMixedNumber  plumbing: resets the alignment field, reads the numerator and
                                                                     the denominator of the fraction and hands them on
  hop 2 stat.inference.TTestImpl      1053 lines  appendMixedNumber  pass-through
  hop 3 linear.RealMatrixImpl         1035 lines  writeMixedNumber   pass-through
  hop 4 util.MathUtils                 740 lines  formatMixed        pass-through
  hop 5 util.ResizableDoubleArray      688 lines  appendMixedForm    GOLD: whole part and remainder of the division, the decision to
                                                                     write the whole part, the remainder's sign rule, and the three
                                                                     formatted numbers with their separators
Host newline counts 1318, 1053, 1035, 740, 688; the smallest host is ResizableDoubleArray (688 lines, the gold host). All five are public
concrete top-level classes in which a public static method compiles. The correct configuration writes exactly the original text for
every Fraction (the alignment reset is done once, before any number is written, as in the original).

Fault (one-line omission of a special-case step in the gold): the step that writes the remainder by its size once a whole part has
been written (`remainder = Math.abs(remainder);`) is dropped, so a negative fraction of size greater than one is written with a minus
sign on both the whole part and the numerator ("-1 -2 / 3" for -5/3). The gold then reads as the ordinary routine "whole part and
remainder of the integer division, whole part left out when zero, remainder over the denominator". Trigger: the EXISTING test
FractionFormatTest::testFormatImproperNegative: properFormat.format(new Fraction(-5, 3)) gives "-1 -2 / 3" instead of "-1 2 / 3".
It is the only test that newly fails: the other four format tests use 1/2, -1/2 (whole part 0: the numerator keeps its sign, as
before), 0/1 and 5/3, on which the variant writes the same text; no production code outside the fraction package uses
ProperFractionFormat, FractionFormat.formatFraction uses the improper instance, and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the fraction appended in proper form: whole part, a space, the remainder over the
denominator; a zero whole part left out) and is silent on signs; "-1 -2 / 3" is not the proper form of -5/3. The convention is pinned
outside the gold: the class javadoc of ProperFractionFormat and the javadoc of ProperFractionFormat.parse ("Minus signs are only allowed
in the whole number part - i.e., "-3 1/2" is legitimate and denotes -7/2, but "-3 -1/2" is invalid"); ProperFractionFormat.parse rejects
a negative numerator after a whole part ("minus signs should be leading") and rebuilds the value as (|w| * d + n) * MathUtils.sign(w);
FractionFormatTest::testParseProperNegative ("-1 2 / 3" reads as -5/3) and testParseProperInvalidMinus ("2 -2 / 3" is rejected) pass;
testFormatNegative (through the chain: -1/2 keeps the minus on the numerator when there is no whole part) passes. So the variant's
output of -5/3 cannot even be read back by the same format.

Single owner: only the gold computes the whole part and the remainder and decides how each is written; hops 2-4 pass the two ints, the
three formats, the buffer and the alignment field along unchanged, hop 1 only resets the alignment field and reads the numerator and the
denominator of the fraction. A change of the two ints above the gold cannot restore the text: the gold writes the denominator it is
given, so the denominator must stay 3, and no numerator n with n / 3 == -1 gives n % 3 == 2 under Java's truncating division; the size
of the numerator loses the minus sign of the whole part. Declared alternatives (G9): hop 1 hands on the numerator of fraction.abs();
hop 2 moves the sign of the fraction onto the denominator; hop 4 hands on the size of the numerator. Each leaves the trigger failing.
Recorded edit that is not consistent with the hops' documentation (not declared, since it passes the suite): a hop above the gold
(for example hop 3) that appends a literal '-' to the buffer itself for a negative numerator and hands on Math.abs(numerator). That
writes the minus sign of the whole number outside the whole format, against every hop's "Each number in the result is written by its
own format" and the class javadoc's configurable format "for each of the whole number, numerator and, denominator" (a whole format
with another negative prefix is then bypassed), and it hands on a value that is not "the numerator of the fraction" (@param of hops
2-5); checked on the variant in a scratch copy (/private/tmp/d4j-mi-Math-106-trick): trigger passes, full suite 0 failing tests. B-0: a hop that re-implements the whole computation (or appends a second, rewritten text) makes the gold's output dead.

Lie: the facade's javadoc claims the whole number is found by repeatedly subtracting the denominator from the numerator and that the
count of subtractions is written before what is left; the chain subtracts nothing (one integer division and one remainder). It names
neither signs, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (as GOLD_TEXT below, with `remainder = Math.abs(remainder);` inside the whole != 0 branch):
  T1 absent: numerator seeds whole and remainder; denominator divides and is written; wholeFormat, numeratorFormat, denominatorFormat
     each write one number; toAppendTo receives every write and is returned; pos is the alignment argument of the three format calls;
     the gold has no argument check.
  T2 absent: whole is read by the decision and written; remainder is reassigned by the sign step and written; no literal-initialised
     local; no loop; the one decision has a real effect (whole part and space written or not).
  T3 absent: the three formats each write their part and both separators are present; the sign step treats only the remainder, but
     the whole part and the remainder do not share a role in the proper form (the whole part carries the sign of the fraction, the
     remainder is the part over the denominator), so they are not a two-member set; no enum, type code or named format member is
     left out.
  T4 absent: "in proper form: the whole part, a space and the remainder over the denominator", "A whole part of zero is left out",
     "written with the whole, numerator and denominator formats", "separated by \" / \"" and "@return the value passed in as
     toAppendTo" are each met by a line of the body; the @param clauses name no rule.
 Variant gold (javadoc, signature, whole = numerator / denominator, remainder = numerator % denominator, whole part and space written
 when whole != 0, remainder, " / " and denominator written, buffer returned):
  T1 absent: numerator seeds whole and remainder; denominator divides and is written by denominatorFormat; wholeFormat writes the whole
     part, numeratorFormat the remainder; toAppendTo receives every write and is returned; pos is passed to the three format calls.
  T2 absent: whole is read by the decision and written; remainder is written; both are computed from the parameters (neither is
     literal-initialised); there is no loop, cursor, counter, flag or best-so-far; the decision writes the whole part and a space or
     not, so it is not dead.
  T3 absent: the three parts are each written by their own format and both separators are present; no sign, absolute-value or
     range-end treatment remains for any part ("No member handled"); the gold's text names no class ("positive", "sign", "absolute",
     "non-negative") that it would handle in part.
  T4 absent: "Appends a fraction ... in proper form: the whole part, a space and the remainder over the denominator" is a general
     description that the body's writes address (like "the reduced fraction"); "A whole part of zero is left out" is met by the
     whole != 0 decision; "written with the whole, numerator and denominator formats respectively" and "separated by \" / \"" by the
     three format calls and the append; "@return the value passed in as toAppendTo" by the return; "@param pos On input: an alignment
     field, if desired. On output: the offsets of the alignment field" by passing pos to every format call; no inline comment; the
     identifiers whole and remainder name what they hold."""

BM = "src/java/org/apache/commons/math/linear/BigMatrixImpl.java"
TT = "src/java/org/apache/commons/math/stat/inference/TTestImpl.java"
RM = "src/java/org/apache/commons/math/linear/RealMatrixImpl.java"
MU = "src/java/org/apache/commons/math/util/MathUtils.java"
RD = "src/java/org/apache/commons/math/util/ResizableDoubleArray.java"
PF = "src/java/org/apache/commons/math/fraction/ProperFractionFormat.java"

GOLD_TEXT = '''/**
 * Appends a fraction, given by its numerator and denominator, to a buffer
 * in proper form: the whole part, a space, and the remainder over the
 * denominator.  A whole part of zero is left out.
 * <p>
 * The whole part, the remainder and the denominator are written with the
 * whole, numerator and denominator formats respectively, and the remainder
 * and the denominator are separated by <code>" / "</code>.
 *
 * @param numerator the numerator of the fraction
 * @param denominator the denominator of the fraction
 * @param wholeFormat the format used for the whole part
 * @param numeratorFormat the format used for the remainder
 * @param denominatorFormat the format used for the denominator
 * @param toAppendTo where the text is to be appended
 * @param pos On input: an alignment field, if desired. On output: the
 *            offsets of the alignment field
 * @return the value passed in as toAppendTo
 */
public static StringBuffer appendMixedForm(int numerator, int denominator,
        NumberFormat wholeFormat, NumberFormat numeratorFormat,
        NumberFormat denominatorFormat, StringBuffer toAppendTo,
        FieldPosition pos) {
    int whole = numerator / denominator;
    int remainder = numerator % denominator;
    if (whole != 0) {
        wholeFormat.format(whole, toAppendTo, pos);
        toAppendTo.append(' ');
        remainder = Math.abs(remainder);
    }
    numeratorFormat.format(remainder, toAppendTo, pos);
    toAppendTo.append(" / ");
    denominatorFormat.format(denominator, toAppendTo, pos);
    return toAppendTo;
}'''

HOP1 = '''/**
 * Formats a fraction in proper form, appending the text to the given
 * buffer.
 * <p>
 * The alignment field is reset to the start of the text, and the numerator
 * and the denominator of the fraction are handed on to be written.  Each
 * number in the result is written by its own format.
 *
 * @param fraction  the fraction to format
 * @param wholeFormat  the format for the whole part
 * @param numeratorFormat  the format for the numerator
 * @param denominatorFormat  the format for the denominator
 * @param toAppendTo  where the text is to be appended
 * @param pos  On input: an alignment field, if desired. On output: the
 *             offsets of the alignment field
 * @return the value passed in as toAppendTo
 */
public static StringBuffer formatMixedNumber(Fraction fraction,
        NumberFormat wholeFormat, NumberFormat numeratorFormat,
        NumberFormat denominatorFormat, StringBuffer toAppendTo,
        FieldPosition pos) {
    pos.setBeginIndex(0);
    pos.setEndIndex(0);
    return TTestImpl.appendMixedNumber(fraction.getNumerator(), fraction.getDenominator(), wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);
}'''

HOP2 = '''/**
 * Appends a fraction, given by its numerator and denominator, to a buffer
 * in proper form.  Each number in the result is written by its own format.
 *
 * @param numerator the numerator of the fraction
 * @param denominator the denominator of the fraction
 * @param wholeFormat the format for the whole part
 * @param numeratorFormat the format for the numerator
 * @param denominatorFormat the format for the denominator
 * @param toAppendTo where the text is to be appended
 * @param pos on input: an alignment field, if desired; on output: the
 * offsets of the alignment field
 * @return the value passed in as toAppendTo
 */
public static StringBuffer appendMixedNumber(int numerator, int denominator,
    NumberFormat wholeFormat, NumberFormat numeratorFormat,
    NumberFormat denominatorFormat, StringBuffer toAppendTo,
    FieldPosition pos) {
    return RealMatrixImpl.writeMixedNumber(numerator, denominator, wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);
}'''

HOP3 = '''/**
 * Writes a fraction, given by its numerator and denominator, to a buffer
 * in proper form.  Each number in the result is written by its own format.
 *
 * @param numerator the numerator of the fraction
 * @param denominator the denominator of the fraction
 * @param wholeFormat the format for the whole part
 * @param numeratorFormat the format for the numerator
 * @param denominatorFormat the format for the denominator
 * @param toAppendTo where the text is to be appended
 * @param pos the alignment field
 * @return the value passed in as toAppendTo
 */
public static StringBuffer writeMixedNumber(int numerator, int denominator,
        NumberFormat wholeFormat, NumberFormat numeratorFormat,
        NumberFormat denominatorFormat, StringBuffer toAppendTo,
        FieldPosition pos) {
    return MathUtils.formatMixed(numerator, denominator, wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);
}'''

HOP4 = '''/**
 * Formats a fraction, given by its numerator and denominator, in proper
 * form, appending the text to a buffer.  Each number in the result is
 * written by its own format.
 *
 * @param numerator the numerator of the fraction
 * @param denominator the denominator of the fraction
 * @param wholeFormat the format for the whole part
 * @param numeratorFormat the format for the numerator
 * @param denominatorFormat the format for the denominator
 * @param toAppendTo where the text is to be appended
 * @param pos the alignment field
 * @return the value passed in as toAppendTo
 */
public static StringBuffer formatMixed(int numerator, int denominator,
        NumberFormat wholeFormat, NumberFormat numeratorFormat,
        NumberFormat denominatorFormat, StringBuffer toAppendTo,
        FieldPosition pos) {
    return ResizableDoubleArray.appendMixedForm(numerator, denominator, wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);
}'''

DESIGN = {
 "instance": "Math-106", "project": "Math", "bug_id": 106, "seed": 6646,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": PF, "class": "org.apache.commons.math.fraction.ProperFractionFormat", "method": "format", "near_line": 86},
 "facade_variant": "V1",
 "state_passed": "getWholeFormat(), getNumeratorFormat(), getDenominatorFormat() (the private format fields, read through the "
                 "class's public getters) plus the parameters fraction, toAppendTo and pos, handed to hop 1; no write-back",
 "reachability_probe": "FractionFormatTest testFormat, testFormatNegative, testFormatZero, testFormatImproper and "
                       "testFormatImproperNegative each fail with java.lang.IllegalStateException: PROBE-REACHED at "
                       "ProperFractionFormat.format(ProperFractionFormat.java:88) from FractionFormat.format(FractionFormat.java:202)",
 "host_mode": "largest5",
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/math/fraction/FractionFormatTest.java",
             "test_class": "org.apache.commons.math.fraction.FractionFormatTest", "test_method": "testFormatImproperNegative"},
 "expected_signature": "expected:<-1 []2 / 3> but was:<-1 [-]2 / 3>",
 "gold": {"method": "appendMixedForm", "text": GOLD_TEXT,
          "fault": {"old": "            toAppendTo.append(' ');\n"
                           "            remainder = Math.abs(remainder);\n"
                           "        }\n",
                    "new": "            toAppendTo.append(' ');\n"
                           "        }\n"}},
 "chain": {
   "facade_body": "return org.apache.commons.math.linear.BigMatrixImpl.formatMixedNumber(fraction, getWholeFormat(), "
                  "getNumeratorFormat(), getDenominatorFormat(), toAppendTo, pos);",
   "lie": "The whole number is found by repeatedly subtracting the denominator from the numerator, and the count of "
          "subtractions is written before what is left.",
   "hops": [
     {"file": BM, "class": "org.apache.commons.math.linear.BigMatrixImpl", "method": "formatMixedNumber",
      "imports": ["java.text.FieldPosition", "java.text.NumberFormat", "org.apache.commons.math.fraction.Fraction",
                  "org.apache.commons.math.stat.inference.TTestImpl"], "text": HOP1},
     {"file": TT, "class": "org.apache.commons.math.stat.inference.TTestImpl", "method": "appendMixedNumber",
      "imports": ["java.text.FieldPosition", "java.text.NumberFormat", "org.apache.commons.math.linear.RealMatrixImpl"],
      "text": HOP2},
     {"file": RM, "class": "org.apache.commons.math.linear.RealMatrixImpl", "method": "writeMixedNumber",
      "imports": ["java.text.FieldPosition", "java.text.NumberFormat"], "text": HOP3},
     {"file": MU, "class": "org.apache.commons.math.util.MathUtils", "method": "formatMixed",
      "imports": ["java.text.FieldPosition", "java.text.NumberFormat"], "text": HOP4},
     {"file": RD, "class": "org.apache.commons.math.util.ResizableDoubleArray", "method": "appendMixedForm",
      "imports": ["java.text.FieldPosition", "java.text.NumberFormat"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math.fraction.ProperFractionFormat::parse",
              "org.apache.commons.math.util.MathUtils::sign",
              "org.apache.commons.math.fraction.FractionFormat::format"],
 "ownership_reason": "Only the gold computes the whole part and the remainder of the division and decides how each is written "
                     "(whole part and space only when the whole part is not zero, the remainder over the denominator); hops 2-4 "
                     "pass the two ints, the three formats, the buffer and the alignment field along unchanged, and hop 1 only "
                     "resets the alignment field and reads the numerator and the denominator of the fraction. The gold's javadoc "
                     "promises the fraction in proper form, which \"-1 -2 / 3\" is not for -5/3. No change of the two ints above "
                     "the gold restores it: the gold writes the denominator it receives, so it must stay 3, and no numerator n "
                     "has n / 3 == -1 and n % 3 == 2 under truncating division; the size of the numerator drops the minus of the "
                     "whole part. The convention is pinned outside the gold: the class javadoc of ProperFractionFormat and the "
                     "javadoc of ProperFractionFormat.parse ('Minus signs are only allowed in the whole number part - i.e., "
                     "\"-3 1/2\" is legitimate and denotes -7/2, but \"-3 -1/2\" is invalid'); ProperFractionFormat.parse rejects "
                     "a negative numerator after the whole part ('minus signs should be leading') and rebuilds the value as "
                     "(|w| * d + n) * MathUtils.sign(w), so the variant's text for -5/3 cannot be read back by the same format; "
                     "FractionFormat.format (the improper form) writes the numerator with its sign when there is no whole part, "
                     "as the gold does. Passing tests: FractionFormatTest testParseProperNegative (\"-1 2 / 3\" is -5/3), "
                     "testParseProperInvalidMinus (\"2 -2 / 3\" is rejected) and testFormatNegative (through the chain: -1/2 is "
                     "written \"-1 / 2\").",
 "ownership_tests": ["org.apache.commons.math.fraction.FractionFormatTest::testParseProperNegative",
                     "org.apache.commons.math.fraction.FractionFormatTest::testParseProperInvalidMinus",
                     "org.apache.commons.math.fraction.FractionFormatTest::testFormatNegative"],
 "compensating": {
   "chain": [
     {"file": BM, "old": "return TTestImpl.appendMixedNumber(fraction.getNumerator(), fraction.getDenominator(), wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);",
      "new": "return TTestImpl.appendMixedNumber(fraction.abs().getNumerator(), fraction.getDenominator(), wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);",
      "why": "hop 1 hands on the numerator of the absolute value of the fraction"},
     {"file": TT, "old": "return RealMatrixImpl.writeMixedNumber(numerator, denominator, wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);",
      "new": "return RealMatrixImpl.writeMixedNumber(Math.abs(numerator), numerator < 0 ? -denominator : denominator, wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);",
      "why": "hop 2 moves the sign of the fraction onto the denominator"},
     {"file": MU, "old": "return ResizableDoubleArray.appendMixedForm(numerator, denominator, wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);",
      "new": "return ResizableDoubleArray.appendMixedForm(Math.abs(numerator), denominator, wholeFormat, numeratorFormat, denominatorFormat, toAppendTo, pos);",
      "why": "hop 4 hands on the size of the numerator"},
   ],
 },
 "host_notes": "host_mode largest5 (batch9_tasks.json hosts_hop_order, used exactly in that order; none substituted, none drawn by "
               "this builder): linear.BigMatrixImpl (hop 1, 1318 lines), stat.inference.TTestImpl (hop 2, 1053), "
               "linear.RealMatrixImpl (hop 3, 1035), util.MathUtils (hop 4, 740), util.ResizableDoubleArray (hop 5, gold, 688; "
               "the smallest host). All five are public concrete top-level classes in which a public static method compiles "
               "(MathUtils is final with a private constructor, which does not affect a static method); the facade's file "
               "fraction/ProperFractionFormat.java is excluded. Anchors from stageB_lib.pick_anchor "
               "(host_search.pick_insertion_anchor) with seed 6646 + 100 + i, as mr3_spec.py inserts them: hop 1 after getEntry "
               "(line idx 702, seed 6746), hop 2 after pairedTTest (155, 6747), hop 3 after hashCode (922, 6748), hop 4 after "
               "cosh (203, 6749), hop 5 after the constructor ResizableDoubleArray(int, float) (186, 6750). The facade calls hop 1 "
               "by its fully-qualified name; each hop imports java.text.NumberFormat and java.text.FieldPosition; hop 1 imports "
               "fraction.Fraction and the next host TTestImpl, hop 2 imports RealMatrixImpl; RealMatrixImpl already imports "
               "MathUtils; MathUtils and ResizableDoubleArray share a package.",
}
