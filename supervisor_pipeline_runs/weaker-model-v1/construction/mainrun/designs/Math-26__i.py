"""Main run Math-26__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
Math-26; the real bug modified org.apache.commons.math3.fraction.Fraction, the target class). Batch 8: no static pair.

Facade: Fraction.toString() (allowed instance target of BATCH8_PREREGISTRATION.md for Math-26__i; facade_planned_by null, no
facade reuse). The other allowed target, Fraction.abs(), was not used: its whole computation is one sign decision that returns the
receiver or its negation, and abs is idempotent, so any hop above a gold that omits the decision could hand the gold an already
non-negative fraction and absorb the fault (no single owner); a one-line omission that keeps the receiver identity of the
original leaves nothing else to omit.
Original computation of the facade: denominator 1 gives Integer.toString(numerator); else numerator 0 gives "0"; else
numerator + " / " + denominator.

facade_variant: V1 (state as parameters). The method reads two private fields and writes none: the facade reads numerator and
denominator (inside Fraction, so no visibility change), passes the two int values to hop 1 and returns the String the chain
returns. No public method of the receiver is needed (no V2), no private method is called (no V4), no package-private type is
involved (no V3/V5). No signature, modifier, @Override or throws change; no new type; no reflection; no test edit.
state_passed: the private final fields numerator and denominator (int values) to hop 1; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Math-26-probe/w of the fixture,
the first statement of toString was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`. `defects4j test -t
org.apache.commons.math3.fraction.FractionTest::testToString`: 1 failing test, java.lang.IllegalStateException: PROBE-REACHED at
Fraction.toString(Fraction.java:650) called from FractionTest.testToString(FractionTest.java:597). Full suite with the probe: 3
failing tests, FractionTest::testToString, BlockFieldMatrixTest::testToString and FieldMatrixImplTest::testToString (the two
matrix tests print matrices whose entries are the whole numbers 0, 1, 2, 3, 5 and 8, through AbstractFieldMatrix.toString).

Hosts (host_mode = "1500"; `mr_lib.py preview Math-26 org/apache/commons/math3/fraction/Fraction.java 5` with the instance seed 3455,
used in draw order, none substituted):
  hop 1 linear.BlockFieldMatrix            1549 lines  fractionText      decision: a zero numerator gives "0" (the original's
                                                                         zero case), otherwise pass-through
  hop 2 optimization.direct.BOBYQAOptimizer 2485 lines ratioText         pass-through
  hop 3 util.FastMath                      3777 lines  toFractionString  pass-through
  hop 4 dfp.Dfp                            2494 lines  fractionAsString  pass-through
  hop 5 linear.BlockRealMatrix             1536 lines  fractionString    GOLD: writes the numerator, and for a denominator other
                                                                         than one the separator and the denominator
Host newline counts 1549, 2485, 3777, 2494, 1536; the smallest host is BlockRealMatrix (1536 lines), which is the gold host.
The correct configuration returns the original String for every Fraction: numerator 0 gives "0" at hop 1 (the original gives "0"
on both of its paths for a zero numerator), denominator 1 gives the numerator alone, every other fraction gives
numerator + " / " + denominator.

Fault (one-line omission inside the gold's decision for a denominator other than one): the line that appends the separator " / "
is dropped, so a fraction that is not a whole number is written as its numerator digits followed directly by its denominator
digits (2/3 becomes "23"). Whole numbers and zero are unchanged. Trigger: the EXISTING test FractionTest::testToString; its first
two assertions ("0" for 0/3 and "3" for 6/2) hold and assertEquals("2 / 3", new Fraction(18, 27).toString()) at line 599 fails
with expected:<2[ / ]3> but was:<2[]3>. It is the only test that newly fails: the probe shows the only other tests that reach
toString are the two matrix toString tests, whose entries are all whole numbers, and the new hops have no other caller.

The gold's javadoc states the idiomatic contract (the String form of a fraction given by numerator and denominator; a
denominator of one gives a whole number) and is silent on the separator; "23" is not the String form of 2/3. The convention is
pinned outside the gold: the facade's own javadoc ('"num / dem" or just "num" if the denominator is one', kept unchanged);
BigFraction.toString, the sibling implementation (numerator + " / " + denominator, the whole number alone for a denominator of
one); FractionFormat.format, which writes the numerator, " / " and the denominator, with FractionFormatTest testFormat ("1 / 2")
and testFormatImproper ("5 / 3") and BigFractionFormatTest testFormat ("1 / 2") passing.

Single owner: only the gold writes the String; hops 2-4 pass the two ints along unchanged and hop 1 only answers a zero
numerator with "0". No pair of ints handed to the variant gold produces "2 / 3" (it never writes a separator), so no one-line
change of the arguments above the gold passes the trigger. Declared alternatives (G9): hop 1 answers whole numbers itself;
hop 3 passes the size of the denominator; hop 4 trims the gold's String. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's result with another implementation, not repairs of the chain):
 B-1 a hop (or the facade) writes the non-whole form itself, e.g. at hop 4
     `return denominator == 1 ? BlockRealMatrix.fractionString(numerator, denominator) : numerator + " / " + denominator;`,
     a second implementation of the gold's writing that makes the gold's output dead for every non-whole fraction.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie placement: the recipe's rewrite_facade appends the lie only to a javadoc that directly precedes the method header; the
javadoc of toString is separated from the header by its @Override annotation, so rewrite_facade finds no javadoc and adds
nothing. The same sentence is therefore added by a comment-only pre_edit (chain geometry) at the end of the javadoc's description
paragraph, in the facade's own voice; chain.lie holds the identical sentence. The @Override annotation, the signature and the
modifiers are unchanged.
Lie: the facade's javadoc claims the numerator and the denominator are first divided by their greatest common divisor, found
with Euclid's algorithm, before they are written; the chain computes no divisor and divides nothing (the stored fields are
written as they are). It names neither the separator, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (a StringBuilder gets the numerator; if denominator != 1 it gets " / " and the denominator; its String is returned):
  T1 absent: numerator is appended to the returned text; denominator decides the branch and is appended; no argument check.
  T2 absent: text is appended to and returned; no literal-initialised local; no loop; the decision appends (its two outcomes
     give different Strings).
  T3 absent: both halves of the pair (numerator and denominator) are written; the gold names no class; no enum or type code.
  T4 absent: 'the String form of a fraction given by its numerator and denominator' is a general description the appends address;
     'a fraction whose denominator is one is written as a whole number' is met (denominator 1 appends only the numerator);
     @param/@return name no concrete rule; no inline comment; identifiers text, numerator, denominator name what they hold.
 Variant gold (text.append(numerator); if (denominator != 1) { text.append(denominator); } return text.toString();):
  T1 absent: numerator is appended to the returned text; denominator decides the branch and is appended to the returned text.
  T2 absent: text is live (appended to, returned); no literal-initialised local, no loop, cursor, counter, flag or best-so-far;
     the decision is live (with it the denominator is appended, without it not).
  T3 absent: both halves of the pair are written (numerator always, denominator in the branch); no member of an enumeration,
     type code or named format is handled while a sibling is not; the gold's text names no class it handles in part.
  T4 absent: 'Returns the string form of a fraction given by its numerator and denominator' is a general description the body
     addresses (it writes the numerator and the denominator); 'A fraction whose denominator is one is written as a whole number'
     is met by the branch; '@param numerator/denominator Numerator/Denominator of the fraction.' and '@return the string form of
     the fraction.' name no concrete rule, limit, value class or property; no inline comment."""

FR = "src/main/java/org/apache/commons/math3/fraction/Fraction.java"
BFM = "src/main/java/org/apache/commons/math3/linear/BlockFieldMatrix.java"
BOB = "src/main/java/org/apache/commons/math3/optimization/direct/BOBYQAOptimizer.java"
FM = "src/main/java/org/apache/commons/math3/util/FastMath.java"
DFP = "src/main/java/org/apache/commons/math3/dfp/Dfp.java"
BRM = "src/main/java/org/apache/commons/math3/linear/BlockRealMatrix.java"

GOLD_TEXT = '''/**
 * Returns the string form of a fraction given by its numerator and
 * denominator.
 * A fraction whose denominator is one is written as a whole number.
 *
 * @param numerator Numerator of the fraction.
 * @param denominator Denominator of the fraction.
 * @return the string form of the fraction.
 */
public static String fractionString(final int numerator, final int denominator) {
    final StringBuilder text = new StringBuilder();
    text.append(numerator);
    if (denominator != 1) {
        text.append(" / ");
        text.append(denominator);
    }
    return text.toString();
}'''

HOP1 = '''/**
 * Get the string form of a fraction given by its numerator and denominator.
 * <p>A zero numerator gives "0".</p>
 * @param numerator numerator of the fraction
 * @param denominator denominator of the fraction
 * @return string form of the fraction
 */
public static String fractionText(final int numerator, final int denominator) {
    if (numerator == 0) {
        return "0";
    }
    return BOBYQAOptimizer.ratioText(numerator, denominator);
}'''

HOP2 = '''/**
 * Gets the string form of a fraction given by its numerator and denominator.
 *
 * @param numerator Numerator of the fraction.
 * @param denominator Denominator of the fraction.
 * @return the string form of the fraction.
 */
public static String ratioText(int numerator, int denominator) {
    return FastMath.toFractionString(numerator, denominator);
}'''

HOP3 = '''/** Get the string form of a fraction given by its numerator and denominator.
 * @param numerator numerator of the fraction
 * @param denominator denominator of the fraction
 * @return string form of the fraction
 */
public static String toFractionString(final int numerator, final int denominator) {
    return Dfp.fractionAsString(numerator, denominator);
}'''

HOP4 = '''/** Get a string representation of a fraction given by its numerator and denominator.
 * @param numerator numerator of the fraction
 * @param denominator denominator of the fraction
 * @return string representation of the fraction
 */
public static String fractionAsString(final int numerator, final int denominator) {
    return BlockRealMatrix.fractionString(numerator, denominator);
}'''

DESIGN = {
 "instance": "Math-26", "project": "Math", "bug_id": 26, "seed": 3455,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i",
 "facade_variant": "V1",
 "state_passed": "private final fields numerator and denominator (int values) to hop 1; no write-back",
 "host_mode": "1500",
 "host_lines": [1549, 2485, 3777, 2494, 1536],
 "reachability_probe": "toString first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-Math-26-probe/w: FractionTest::testToString fails with PROBE-REACHED at "
                       "Fraction.toString(Fraction.java:650) from FractionTest.java:597; full suite with the probe: 3 failing tests "
                       "(FractionTest::testToString, BlockFieldMatrixTest::testToString, FieldMatrixImplTest::testToString; the "
                       "matrix tests print whole-number entries only)",
 "facade": {"file": FR, "class": "org.apache.commons.math3.fraction.Fraction", "method": "toString", "near_line": 649},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/math3/fraction/FractionTest.java",
             "test_class": "org.apache.commons.math3.fraction.FractionTest", "test_method": "testToString"},
 "expected_signature": "expected:<2[ / ]3> but was:<2[]3>",
 "gold": {"method": "fractionString", "text": GOLD_TEXT,
          "fault": {"old": "            text.append(\" / \");\n"
                           "            text.append(denominator);\n",
                    "new": "            text.append(denominator);\n"}},
 "pre_edits": {"chain": [
   {"file": FR,
    "old": "     * \"num / dem\" or just \"num\" if the denominator is one.\n     * </p>\n",
    "new": "     * \"num / dem\" or just \"num\" if the denominator is one.\n"
           "     * The numerator and the denominator are first divided by their greatest\n"
           "     * common divisor, found with Euclid's algorithm, before they are written.\n"
           "     * </p>\n"},
 ]},
 "chain": {
   "facade_body": "return org.apache.commons.math3.linear.BlockFieldMatrix.fractionText(numerator, denominator);",
   "lie": "The numerator and the denominator are first divided by their greatest common divisor, found with Euclid's "
          "algorithm, before they are written.",
   "hops": [
     {"file": BFM, "class": "org.apache.commons.math3.linear.BlockFieldMatrix", "method": "fractionText",
      "imports": ["org.apache.commons.math3.optimization.direct.BOBYQAOptimizer"], "text": HOP1},
     {"file": BOB, "class": "org.apache.commons.math3.optimization.direct.BOBYQAOptimizer", "method": "ratioText",
      "imports": ["org.apache.commons.math3.util.FastMath"], "text": HOP2},
     {"file": FM, "class": "org.apache.commons.math3.util.FastMath", "method": "toFractionString",
      "imports": ["org.apache.commons.math3.dfp.Dfp"], "text": HOP3},
     {"file": DFP, "class": "org.apache.commons.math3.dfp.Dfp", "method": "fractionAsString",
      "imports": ["org.apache.commons.math3.linear.BlockRealMatrix"], "text": HOP4},
     {"file": BRM, "class": "org.apache.commons.math3.linear.BlockRealMatrix", "method": "fractionString", "imports": [],
      "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.math3.fraction.BigFraction::toString",
              "org.apache.commons.math3.fraction.FractionFormat::format",
              "org.apache.commons.math3.fraction.ProperFractionFormat::format"],
 "ownership_reason": "Only the gold writes the String of the fraction; hops 2-4 pass the numerator and the denominator along "
                     "unchanged and hop 1 only answers a zero numerator with \"0\". The gold's javadoc promises the string form "
                     "of the fraction given by its numerator and denominator, which \"23\" is not for 2/3 (it is the string "
                     "form of the whole number twenty-three). No one-line change of the two ints above the gold restores the "
                     "form: the variant gold never writes a separator, so no argument pair yields \"2 / 3\". The convention is "
                     "pinned outside the gold: the facade's own javadoc ('\"num / dem\" or just \"num\" if the denominator is "
                     "one'); BigFraction.toString, the sibling implementation, writes numerator + \" / \" + denominator and the "
                     "numerator alone for a denominator of one; FractionFormat.format and ProperFractionFormat.format write the "
                     "numerator, \" / \" and the denominator (FractionFormatTest testFormat \"1 / 2\" and testFormatImproper "
                     "\"5 / 3\", BigFractionFormatTest testFormat \"1 / 2\").",
 "ownership_tests": ["org.apache.commons.math3.fraction.FractionFormatTest::testFormat",
                     "org.apache.commons.math3.fraction.FractionFormatTest::testFormatImproper",
                     "org.apache.commons.math3.fraction.BigFractionFormatTest::testFormat"],
 "compensating": {
   "chain": [
     {"file": BFM, "old": "return BOBYQAOptimizer.ratioText(numerator, denominator);",
      "new": "return denominator == 1 ? Integer.toString(numerator) : BOBYQAOptimizer.ratioText(numerator, denominator);",
      "why": "hop 1 answers whole numbers itself and passes only the other fractions on"},
     {"file": FM, "old": "return Dfp.fractionAsString(numerator, denominator);",
      "new": "return Dfp.fractionAsString(numerator, FastMath.abs(denominator));",
      "why": "hop 3 passes the size of the denominator"},
     {"file": DFP, "old": "return BlockRealMatrix.fractionString(numerator, denominator);",
      "new": "return BlockRealMatrix.fractionString(numerator, denominator).trim();",
      "why": "hop 4 trims the String the gold returns"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are the seeded draw `mr_lib.py preview Math-26 org/apache/commons/math3/fraction/Fraction.java 5` "
               "(seed 3455), in draw order, none substituted: linear.BlockFieldMatrix (hop 1, 1549 lines, anchor after "
               "`getRowMatrix`, seed 3555), optimization.direct.BOBYQAOptimizer (hop 2, 2485, after the constructor "
               "`BOBYQAOptimizer`, 3556), util.FastMath (hop 3, 3777, after `log1p`, 3557), dfp.Dfp (hop 4, 2494, after "
               "`hashCode`, 3558), linear.BlockRealMatrix (hop 5, gold, 1536, after `multiply`, 3559; the smallest host). The "
               "draw notes that the package-distinctness heuristic was relaxed for hosts 5/6 (pool of six usable classes of "
               "1500+ lines; FastMathLiteralArrays is unusable); BlockFieldMatrix and BlockRealMatrix share the linear package. "
               "All five are public top-level classes in which a static method compiles (BlockFieldMatrix is generic; the "
               "static hop names it raw). The facade calls hop 1 by its fully-qualified name; each hop imports the next host. "
               "The facade's class Fraction is excluded from the draw.",
}
