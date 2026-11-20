"""Main run Lang-22__i (cell C10i, batch 7: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Lang-22; the real bug modified Fraction, the target class). Paired static-facade instance: MR-Lang-22 (facade Fraction.getFraction,
excluded here; none of its files were opened).

Facade: Fraction.toProperString() (allowed instance target of BATCH7_PREREGISTRATION.md row 201; no facade reuse). The other two
allowed targets were not used: Fraction.hashCode is one cached expression over two ints (no decision or iteration a quiet one-line
omission could live in without leaving a parameter unused), and Fraction.pow is a recursion over invert/multiplyBy whose
square-and-multiply loop leaves a frozen accumulator or a non-advancing exponent under any one-line omission.
Original computation of the facade (cached in the transient field toProperString): numerator 0 gives "0"; numerator == denominator
gives "1"; numerator == -denominator gives "-1"; if |numerator| > denominator, the proper whole part getProperWhole() (numerator /
denominator, which carries the sign) and the proper numerator getProperNumerator() (Math.abs(numerator % denominator), "always
positive") give the whole number alone when the proper numerator is 0 and "W P/D" otherwise; else (|numerator| < denominator)
"numerator/denominator".

facade_variant: V1 (state as parameters). The method reads two private fields and writes one: the facade keeps the cache check, reads
the private fields numerator and denominator (inside Fraction, so no visibility change), passes the two int values to hop 1 and writes
the returned String back into the cache field toProperString, then returns it. The chain needs no method of the receiver (the proper
parts are plain int arithmetic on the two values), so V2 (receiver as parameter) is not needed; no private method of Fraction is
called (no V4), and no package-private type is involved (no V3/V5). No signature, modifier, override or throws change; no new type;
no reflection; no test edit.
state_passed: the private fields numerator and denominator (int values) to hop 1; write-back of the returned String into the
private transient cache field toProperString.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Lang-22-probe/w of the fixture, the
first statement of toProperString was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }` (the `if (true)` only
keeps the rest of the body reachable for javac). `defects4j test -t org.apache.commons.lang3.math.FractionTest::testToProperString`:
1 failing test, java.lang.IllegalStateException: PROBE-REACHED at Fraction.toProperString(Fraction.java:935) called from
FractionTest.testToProperString(FractionTest.java:1318). Full suite with the probe: 1 failing test (testToProperString only; the
facade has no production caller). The facade is reached by an existing test directly.

Hosts (host_mode = "1500"; hosts_hop_order of bridge7_tasks.json, used in that order; mr_lib.py preview with the instance seed 6893
draws exactly these five in this order, so nothing was substituted):
  hop 1 SystemUtils           1824 lines  toProperFractionString  decision: a zero numerator gives "0" (the original's first case)
  hop 2 builder.ToStringStyle 2269 lines  properFractionText      pass-through
  hop 3 time.FastDateFormat   1757 lines  formatProperFraction    pass-through
  hop 4 StringUtils           6422 lines  properFractionAsString  pass-through
  hop 5 time.DateUtils        1871 lines  properFractionString    GOLD: the whole part and the remainder of the division, the
                                                                  remainder's sign rule, and the decision between the three forms
                                                                  (whole number only, Y/Z only, X Y/Z)
Host newline counts 1824, 2269, 1757, 6422, 1871; the smallest host is FastDateFormat (1757 lines); the gold host has 1871 lines.
The correct configuration returns the original String for every Fraction (denominators are positive for every Fraction the
factories and operations create): remainder == 0 covers numerator 0, +-denominator, Integer.MIN_VALUE/1 and every whole-number
fraction; whole == 0 is exactly |numerator| < denominator, which the original writes as numerator/denominator with its sign; the
remaining fractions get whole + " " + |numerator % denominator| + "/" + denominator, which is getProperWhole() and
getProperNumerator() of the original. Hop 1's zero shortcut gives the same "0" the gold gives.

Fault (one-line omission of a special-case decision in the gold): the decision that turns a negative remainder into its magnitude is
dropped, so a negative fraction greater than one in size is written with the sign twice ("-1 -2/5"). The gold then reads as the
ordinary routine "whole part and remainder of the integer division, written as X, Y/Z or X Y/Z". Trigger: the EXISTING test
FractionTest::testToProperString. Its first seven assertions (3/5, the cache identity, 7/5, 14/10, 4/2, 0/2, 2/2) still hold, and
assertEquals("-1 2/5", f.toProperString()) for getFraction(-7, 5) at line 1338 fails with expected:<-1 []2/5> but was:<-1 [-]2/5>.
It is the only test that newly fails: toProperString has no production caller and no other test calls it (the probe's full-suite
run above), and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the fraction as a proper String in the format X Y/Z, the facade's own wording,
with the two shortened forms) and is silent on signs; "-1 -2/5" is not the proper String of -7/5. The convention is pinned outside
the gold: Fraction.getProperNumerator (javadoc "always positive"; "-7/4 ... resolved into -1 3/4, so this method returns the positive
proper numerator, 3") and Fraction.getProperWhole ("the whole fraction part of a proper fraction, that includes the sign"), with
FractionTest::testGets (getFraction(-3, 5, 6): proper whole -3, proper numerator 5) passing; Fraction.getFraction(String), the reader
of the 'X Y/Z' format, hands X, Y and Z to Fraction.getFraction(int, int, int), whose javadoc says "The negative sign must be passed
in on the whole number part" and which throws ArithmeticException for a negative numerator, so "-1 -2/5" cannot be read back
(FractionTest::testFactory_String_proper reads "-7 1/2" as -15/2 and "-1 2/4" as -6/4; FractionTest::testFactory_int_int_int
rejects getFraction(-1, -6, 10)); the facade's own javadoc ('wholeNumber numerator/denominator', whole number left out when zero,
only the whole number when the numerator is zero) is kept unchanged.

Single owner: only the gold computes the remainder and decides how the fraction is written; hops 2-4 pass the two ints along and
hop 1 only answers a zero numerator. Every one-line change of the two ints above the gold fails the trigger: with Java's truncating
division a positive denominator can never give the variant gold a negative whole part with a positive remainder, a negative
denominator is printed, and a sign written by a caller in front of the size of the numerator breaks on Integer.MIN_VALUE (the
trigger's getFraction(Integer.MIN_VALUE, 0, 1) and getFraction(-1, 1, Integer.MAX_VALUE) cases; -Integer.MIN_VALUE overflows).
Declared alternatives (G9): hop 1 passes the size of the numerator (Math.abs); hop 2 moves the sign onto the denominator; hop 3
writes the sign itself and passes the size of the numerator on. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-1 string surgery on the gold's output at hop 4 (or any hop, or the facade's write-back):
     `return DateUtils.properFractionString(numerator, denominator).replace(" -", " ");` rewrites the String the gold returned with
     a second implementation of its sign rule applied to text; the gold still returns "-1 -2/5" against its own javadoc. Checked
     on the variant in a scratch copy: trigger passes, full suite 0 failing tests.
 B-0 the facade's original body (or a hop re-deriving the parts from Fraction.getFraction(numerator, denominator).getProperWhole()
     and getProperNumerator()) re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc claims the whole number is found first by a binary search over the multiples of the denominator and the
other parts are then appended to it; the chain searches nothing (one integer division and one remainder) and does not build the
String around a whole number first (the shortened forms return without it). It names neither signs, the remainder, the omitted
step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: numerator seeds whole and remainder and is written in the Y/Z form; denominator divides, bounds the remainder and is
     written in both fraction forms; neither is only argument-checked (the gold has no argument check).
  T2 absent: whole is read by a decision and written in two forms; remainder is reassigned by the sign decision and read by the
     zero decision and the X Y/Z form; no literal-initialised local; the three decisions lead to different effects.
  T3 absent: the zero decisions treat both parts (remainder == 0 and whole == 0); the sign decision treats only the remainder,
     but the whole part and the remainder do not have the same role in the format (X carries the sign of the fraction, Y/Z is the
     part that remains), so they are not a two-member set; no enum, type code or named format member is left out.
  T4 absent: 'proper String in the format X Y/Z', 'A whole number of zero is left out' and 'a fraction without a remainder gives
     only the whole number' are each met by a line of the body; the @param clauses name no rule.
 Variant gold (javadoc, signature, whole and remainder of the division, `remainder == 0` gives the whole number, `whole == 0` gives
 numerator/denominator, otherwise whole + " " + remainder + "/" + denominator):
  T1 absent: numerator seeds whole and remainder and is written in the Y/Z form; denominator divides and is written in both
     fraction forms; both decide the return value.
  T2 absent: whole and remainder are both read by a decision and by the returned String; neither is literal-initialised; there is
     no loop, cursor, counter, flag or best-so-far; both decisions return different Strings from the fall-through.
  T3 absent: the zero treatment is given to both parts (remainder == 0, whole == 0) and the three written forms are all present;
     no sign, absolute value or range-end treatment remains for any part ('No member handled'); the gold's text names no class
     (no "positive", "absolute", "sign", "finite") that it would handle in part.
  T4 absent: 'Gets a fraction ... as a proper String in the format X Y/Z' is a general description that the last return addresses
     (like 'the reduced fraction'); 'A whole number of zero is left out' is met by the whole == 0 branch; 'a fraction without a
     remainder gives only the whole number' by the remainder == 0 branch; '@param numerator/denominator the numerator/denominator of
     the fraction' and '@return the proper String form of the fraction' name no concrete rule; no inline comment; the identifiers
     whole and remainder name what they hold (numerator / denominator and numerator % denominator)."""

FR = "src/main/java/org/apache/commons/lang3/math/Fraction.java"
SYS = "src/main/java/org/apache/commons/lang3/SystemUtils.java"
TSS = "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"

GOLD_TEXT = '''/**
 * <p>Gets a fraction, given by its numerator and denominator, as a
 * proper String in the format X Y/Z.</p>
 *
 * <p>A whole number of zero is left out, and a fraction without a
 * remainder gives only the whole number.</p>
 *
 * @param numerator  the numerator of the fraction
 * @param denominator  the denominator of the fraction
 * @return the proper String form of the fraction
 */
public static String properFractionString(int numerator, int denominator) {
    int whole = numerator / denominator;
    int remainder = numerator % denominator;
    if (remainder < 0) {
        remainder = -remainder;
    }
    if (remainder == 0) {
        return Integer.toString(whole);
    }
    if (whole == 0) {
        return numerator + "/" + denominator;
    }
    return whole + " " + remainder + "/" + denominator;
}'''

HOP1 = '''/**
 * <p>
 * Gets a fraction, given by its numerator and denominator, as a proper String in the format X Y/Z.
 * </p>
 *
 * <p>
 * A zero numerator gives <code>"0"</code>.
 * </p>
 *
 * @param numerator
 *            the numerator of the fraction
 * @param denominator
 *            the denominator of the fraction
 * @return the proper String form of the fraction
 */
public static String toProperFractionString(int numerator, int denominator) {
    if (numerator == 0) {
        return "0";
    }
    return ToStringStyle.properFractionText(numerator, denominator);
}'''

HOP2 = '''/**
 * <p>Gets a fraction, given by its numerator and denominator, as a
 * proper <code>String</code> in the format X Y/Z.</p>
 *
 * @param numerator  the numerator of the fraction
 * @param denominator  the denominator of the fraction
 * @return the proper <code>String</code> form of the fraction
 */
public static String properFractionText(int numerator, int denominator) {
    return FastDateFormat.formatProperFraction(numerator, denominator);
}'''

HOP3 = '''/**
 * <p>Formats a fraction, given by its numerator and denominator, as a
 * proper string in the format X Y/Z.</p>
 *
 * @param numerator  the numerator of the fraction
 * @param denominator  the denominator of the fraction
 * @return the formatted string
 */
public static String formatProperFraction(int numerator, int denominator) {
    return StringUtils.properFractionAsString(numerator, denominator);
}'''

HOP4 = '''/**
 * <p>Gets a fraction, given by its numerator and denominator, as a
 * proper String in the format X Y/Z.</p>
 *
 * @param numerator  the numerator of the fraction
 * @param denominator  the denominator of the fraction
 * @return the proper String form of the fraction
 */
public static String properFractionAsString(int numerator, int denominator) {
    return DateUtils.properFractionString(numerator, denominator);
}'''

DESIGN = {
 "instance": "Lang-22", "project": "Lang", "bug_id": 22, "seed": 6893,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": FR, "class": "org.apache.commons.lang3.math.Fraction", "method": "toProperString", "near_line": 934},
 "facade_variant": "V1",
 "state_passed": "private fields numerator and denominator (int values) to hop 1; the returned String is written back into the "
                 "private transient cache field toProperString",
 "reachability_probe": "testToProperString fails with java.lang.IllegalStateException: PROBE-REACHED at "
                       "Fraction.toProperString(Fraction.java:935) from FractionTest.java:1318; full suite with the probe: 1 failing "
                       "test (testToProperString)",
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/math/FractionTest.java",
             "test_class": "org.apache.commons.lang3.math.FractionTest", "test_method": "testToProperString"},
 "expected_signature": "expected:<-1 []2/5> but was:<-1 [-]2/5>",
 "gold": {"method": "properFractionString", "text": GOLD_TEXT,
          "fault": {"old": "        int remainder = numerator % denominator;\n"
                           "        if (remainder < 0) {\n"
                           "            remainder = -remainder;\n"
                           "        }\n",
                    "new": "        int remainder = numerator % denominator;\n"}},
 "chain": {
   "facade_body": "if (toProperString == null) {\n"
                  "            toProperString = org.apache.commons.lang3.SystemUtils.toProperFractionString(numerator, denominator);\n"
                  "        }\n"
                  "        return toProperString;",
   "lie": "The whole number is found first, by a binary search over the multiples of the denominator, and the other parts are "
          "then appended to it.",
   "hops": [
     {"file": SYS, "class": "org.apache.commons.lang3.SystemUtils", "method": "toProperFractionString",
      "imports": ["org.apache.commons.lang3.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "properFractionText",
      "imports": ["org.apache.commons.lang3.time.FastDateFormat"], "text": HOP2},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "formatProperFraction",
      "imports": ["org.apache.commons.lang3.StringUtils"], "text": HOP3},
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "properFractionAsString",
      "imports": ["org.apache.commons.lang3.time.DateUtils"], "text": HOP4},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "properFractionString", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.math.Fraction::getProperNumerator",
              "org.apache.commons.lang3.math.Fraction::getProperWhole",
              "org.apache.commons.lang3.math.Fraction::getFraction"],
 "ownership_reason": "Only the gold computes the remainder of the division and decides how the fraction is written (the whole "
                     "number alone, Y/Z alone, or X Y/Z); hops 2-4 pass the numerator and the denominator along unchanged and "
                     "hop 1 only answers a zero numerator with \"0\". The gold's javadoc promises the fraction as a proper String "
                     "in the format X Y/Z, which \"-1 -2/5\" is not for -7/5. No one-line change of the two ints above the gold "
                     "restores the proper form: with truncating division and a positive denominator the gold can never see a "
                     "negative whole part with a positive remainder, a negative denominator is written into the String, and a "
                     "sign written by a caller in front of the size of the numerator breaks on Integer.MIN_VALUE, which the "
                     "trigger formats twice. The convention is pinned outside the gold: Fraction.getProperNumerator ('always "
                     "positive'; -7/4 is resolved into -1 3/4 and it returns 3) and Fraction.getProperWhole (the whole part "
                     "'that includes the sign'), with FractionTest testGets (getFraction(-3, 5, 6): proper whole -3, proper "
                     "numerator 5); Fraction.getFraction(String), the reader of the 'X Y/Z' format, passes X, Y and Z to "
                     "Fraction.getFraction(int, int, int), which requires 'The negative sign must be passed in on the whole "
                     "number part' and throws ArithmeticException for a negative numerator (FractionTest "
                     "testFactory_String_proper reads \"-7 1/2\" and \"-1 2/4\"; testFactory_int_int_int rejects "
                     "getFraction(-1, -6, 10)); the facade's own javadoc describes the format 'wholeNumber "
                     "numerator/denominator'.",
 "ownership_tests": ["org.apache.commons.lang3.math.FractionTest::testGets",
                     "org.apache.commons.lang3.math.FractionTest::testFactory_String_proper",
                     "org.apache.commons.lang3.math.FractionTest::testFactory_int_int_int"],
 "compensating": {
   "chain": [
     {"file": SYS, "old": "return ToStringStyle.properFractionText(numerator, denominator);",
      "new": "return ToStringStyle.properFractionText(Math.abs(numerator), denominator);",
      "why": "hop 1 passes the size of the numerator and leaves its sign out"},
     {"file": TSS, "old": "return FastDateFormat.formatProperFraction(numerator, denominator);",
      "new": "return FastDateFormat.formatProperFraction(Math.abs(numerator), numerator < 0 ? -denominator : denominator);",
      "why": "hop 2 moves the sign of the fraction onto the denominator"},
     {"file": FDF, "old": "return StringUtils.properFractionAsString(numerator, denominator);",
      "new": "return numerator < 0 ? \"-\" + StringUtils.properFractionAsString(-numerator, denominator) : StringUtils.properFractionAsString(numerator, denominator);",
      "why": "hop 3 writes the sign itself and passes the size of the numerator on"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are hosts_hop_order of the task record (bridge7_tasks.json), in that order, none "
               "substituted; mr_lib.py preview Lang-22 org/apache/commons/lang3/math/Fraction.java 5 with the instance seed 6893 "
               "draws the same five in the same order: SystemUtils (hop 1, 1824 lines), builder.ToStringStyle (hop 2, 2269), "
               "time.FastDateFormat (hop 3, 1757; the smallest host), StringUtils (hop 4, 6422), time.DateUtils (hop 5, gold, "
               "1871). All five are public top-level classes in which a static method compiles (ToStringStyle is abstract, which "
               "does not affect a static method). Anchors from stageB_lib.pick_insertion_anchor with seed 6893 + 100 + i (as "
               "mr3_spec.py inserts them): hop 1 after `isJavaVersionAtLeast` (line idx 1535, seed 6993), hop 2 after `append` "
               "(438, 6994), hop 3 after `format` (833, 6995), hop 4 after `stripToNull` (411, 6996), hop 5 after "
               "`truncatedCompareTo` (1764, 6997); all in the outer class. The facade calls hop 1 by its fully-qualified name; "
               "each hop imports the next host. The facade's class Fraction is not a host.",
}
