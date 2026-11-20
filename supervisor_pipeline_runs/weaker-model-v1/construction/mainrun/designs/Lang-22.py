"""Main-run instance Lang-22 (C10 recipe on the fixed checkout of Defects4J Lang-22; target class Fraction, the class the real bug
modified). Facade = Fraction.getFraction(String) (the pool's 50-line getFraction overload). Its null guard stays; the rest of
its computation is redistributed along five hops in the drawn hosts (seed 6893, draw order, no substitution):
  hop 1 SystemUtils.toFraction        the format dispatch and the integer formats ('X Y/Z', 'Y/Z', 'X'), unchanged; a string with a
                                      dot goes down the decimal path
  hop 2 ToStringStyle.fractionOf      sign, range check and the final reduced Fraction (placement)
  hop 3 FastDateFormat.improperTerms  whole-number split and recombination (aggregation)
  hop 4 StringUtils.fractionalTerms   pass-through for a value in [0, 1)
  hop 5 DateUtils.convergentTerms     GOLD: the continued-fraction iteration over the convergents (the per-element core)
The decimal path computes exactly what Fraction.getFraction(double) computes (same arithmetic, same stopping rules), so the
correct configuration is behaviour-preserving.
Fault: the convergent loop omits its denominator-bound stop (`&& denom2 <= 10000`, one line of the loop condition). For "0.66666"
the expansion then runs past 2/3 to the exact 33333/50000. Trigger: FractionTest::testFactory_String_double (expected:<2> but
was:<33333>). It is the only test that newly fails: FractionTest::testFactory_double calls getFraction(double) directly, which
is unchanged, and no other test parses a string with a dot (fault-isolation checked with a scratch harness over FractionTest).
The bound is pinned outside the gold: Fraction.getFraction(double), the sibling overload, stops at the same bound in its own
loop and documents it ("bounding the denominator by 10,000"); testFactory_double (passing) pins 0.66666 -> 2/3 and
1/10001 -> 0/1 through that sibling. The gold's javadoc states the contract (denominator at most 10,000) and is silent on the
stopping step. Ownership: once the loop has run past the bound the last admissible convergent is gone; no caller can recover
it from the returned pair, and no caller-side rounding of the value restores it (the expansion of any rounded decimal runs to
that decimal's exact fraction; checked: rounding to 4 or 5 places, truncation and a float cast at hops 2/4 all still fail).
Bypass (recorded, not a competing repair under W13): hop 1 or hop 2 can call Fraction.getFraction(double) directly, which is
exactly what the original facade did, discarding hops 2-5 / 3-5.
Lie: the facade's documentation claims a float/power-of-two decimal conversion; the code does a bounded continued-fraction
approximation, and neither the correct (2/3) nor the variant (33333/50000) output matches the lie."""

FRACTION = "src/main/java/org/apache/commons/lang3/math/Fraction.java"

HOP1 = '''/**
 * <p>Creates a <code>Fraction</code> from a <code>String</code> in one of
 * the formats 'X.Y' (a <code>double</code>), 'X Y/Z', 'Y/Z' or 'X' (a
 * simple whole number).</p>
 *
 * @param str  the string to parse, not null
 * @return the new <code>Fraction</code> instance
 * @throws NumberFormatException if the number format is invalid
 * @throws ArithmeticException if the value cannot be represented as a
 *  <code>Fraction</code>
 */
public static Fraction toFraction(String str) {
    // parse double format
    int pos = str.indexOf('.');
    if (pos >= 0) {
        return ToStringStyle.fractionOf(Double.parseDouble(str));
    }

    // parse X Y/Z format
    pos = str.indexOf(' ');
    if (pos > 0) {
        int whole = Integer.parseInt(str.substring(0, pos));
        str = str.substring(pos + 1);
        pos = str.indexOf('/');
        if (pos < 0) {
            throw new NumberFormatException("The fraction could not be parsed as the format X Y/Z");
        } else {
            int numer = Integer.parseInt(str.substring(0, pos));
            int denom = Integer.parseInt(str.substring(pos + 1));
            return Fraction.getFraction(whole, numer, denom);
        }
    }

    // parse Y/Z format
    pos = str.indexOf('/');
    if (pos < 0) {
        // simple whole number
        return Fraction.getFraction(Integer.parseInt(str), 1);
    } else {
        int numer = Integer.parseInt(str.substring(0, pos));
        int denom = Integer.parseInt(str.substring(pos + 1));
        return Fraction.getFraction(numer, denom);
    }
}'''

HOP2 = '''/**
 * <p>Creates a <code>Fraction</code> close to a <code>double</code> value,
 * in reduced form and with a denominator of at most 10,000.</p>
 *
 * @param value  the value to convert
 * @return the new <code>Fraction</code> instance, in reduced form
 * @throws ArithmeticException if <code>|value| &gt; Integer.MAX_VALUE</code>
 *  or <code>value = NaN</code>, or if the conversion does not converge
 */
public static Fraction fractionOf(double value) {
    int sign = (value < 0 ? -1 : 1);
    value = Math.abs(value);
    if (value > Integer.MAX_VALUE || Double.isNaN(value)) {
        throw new ArithmeticException("The value must not be greater than Integer.MAX_VALUE or NaN");
    }
    int[] terms = FastDateFormat.improperTerms(value);
    return Fraction.getReducedFraction(terms[0] * sign, terms[1]);
}'''

HOP3 = '''/**
 * <p>Gets the numerator and the denominator of a fraction close to a
 * non-negative value, with a denominator of at most 10,000 and the whole
 * number part of the value carried in the numerator.</p>
 *
 * @param value  the value to convert, not negative and not greater than
 *  <code>Integer.MAX_VALUE</code>
 * @return a two element array containing the numerator and the denominator
 * @throws ArithmeticException if the conversion does not converge
 */
public static int[] improperTerms(double value) {
    int wholeNumber = (int) value;
    int[] fraction = StringUtils.fractionalTerms(value - wholeNumber);
    return new int[] {fraction[0] + wholeNumber * fraction[1], fraction[1]};
}'''

HOP4 = '''/**
 * <p>Gets the numerator and the denominator of a fraction close to a value
 * between zero and one, with a denominator of at most 10,000.</p>
 *
 * @param value  the value to convert, at least zero and less than one
 * @return a two element array containing the numerator and the denominator
 * @throws ArithmeticException if the conversion does not converge
 */
public static int[] fractionalTerms(double value) {
    return DateUtils.convergentTerms(value);
}'''

GOLD_TEXT = '''/**
 * <p>Gets the numerator and the denominator of a fraction close to a value
 * between zero and one, using the continued fraction algorithm.</p>
 *
 * <p>At most 25 convergents are computed, and the denominator of the
 * fraction is at most 10,000.</p>
 *
 * @param value  the value to convert, at least zero and less than one
 * @return a two element array containing the numerator and the denominator
 * @throws ArithmeticException if the algorithm does not converge
 */
public static int[] convergentTerms(double value) {
    int numer0 = 0;  // the pre-previous
    int denom0 = 1;  // the pre-previous
    int numer1 = 1;  // the previous
    int denom1 = 0;  // the previous
    int numer2 = 0;  // the current
    int denom2 = 0;  // the current
    int a1 = (int) value;
    int a2 = 0;
    double x1 = 1;
    double x2 = 0;
    double y1 = value - a1;
    double y2 = 0;
    double delta1, delta2 = Double.MAX_VALUE;
    double fraction;
    int i = 1;
    do {
        delta1 = delta2;
        a2 = (int) (x1 / y1);
        x2 = y1;
        y2 = x1 - a2 * y1;
        numer2 = a1 * numer1 + numer0;
        denom2 = a1 * denom1 + denom0;
        fraction = (double) numer2 / (double) denom2;
        delta2 = Math.abs(value - fraction);
        a1 = a2;
        x1 = x2;
        y1 = y2;
        numer0 = numer1;
        denom0 = denom1;
        numer1 = numer2;
        denom1 = denom2;
        i++;
    } while (delta1 > delta2
            && denom2 <= 10000
            && denom2 > 0
            && i < 25);
    if (i == 25) {
        throw new ArithmeticException("Unable to convert double to fraction");
    }
    return new int[] {numer0, denom0};
}'''

DESIGN = {
 "instance": "Lang-22", "project": "Lang", "bug_id": 22, "seed": 6893,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": FRACTION, "class": "org.apache.commons.lang3.math.Fraction", "method": "getFraction", "near_line": 324},
 "trigger": {"existing": True, "test_file": "src/test/java/org/apache/commons/lang3/math/FractionTest.java",
             "test_class": "org.apache.commons.lang3.math.FractionTest", "test_method": "testFactory_String_double"},
 "expected_signature": "expected:<2> but was:<33333>",
 "gold": {"method": "convergentTerms", "text": GOLD_TEXT,
          "fault": {"old": "        } while (delta1 > delta2\n                && denom2 <= 10000\n                && denom2 > 0\n                && i < 25);",
                    "new": "        } while (delta1 > delta2\n                && denom2 > 0\n                && i < 25);"}},
 "chain": {
   "facade_body": "if (str == null) {\n            throw new IllegalArgumentException(\"The string must not be null\");\n        }\n        return org.apache.commons.lang3.SystemUtils.toFraction(str);",
   "lie": "A string containing a dot is converted by reading it as a <code>float</code> and placing the binary digits of its mantissa over the matching power of two.",
   "hops": [
     {"file": "src/main/java/org/apache/commons/lang3/SystemUtils.java", "class": "org.apache.commons.lang3.SystemUtils", "method": "toFraction",
      "imports": ["org.apache.commons.lang3.builder.ToStringStyle", "org.apache.commons.lang3.math.Fraction"], "text": HOP1},
     {"file": "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java", "class": "org.apache.commons.lang3.builder.ToStringStyle", "method": "fractionOf",
      "imports": ["org.apache.commons.lang3.math.Fraction", "org.apache.commons.lang3.time.FastDateFormat"], "text": HOP2},
     {"file": "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java", "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "improperTerms",
      "imports": ["org.apache.commons.lang3.StringUtils"], "text": HOP3},
     {"file": "src/main/java/org/apache/commons/lang3/StringUtils.java", "class": "org.apache.commons.lang3.StringUtils", "method": "fractionalTerms",
      "imports": ["org.apache.commons.lang3.time.DateUtils"], "text": HOP4},
     {"file": "src/main/java/org/apache/commons/lang3/time/DateUtils.java", "class": "org.apache.commons.lang3.time.DateUtils", "method": "convergentTerms",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.math.Fraction::getFraction", "org.apache.commons.lang3.math.Fraction::getReducedFraction"],
 "ownership_reason": "Only the convergent loop sees the successive convergents; the 10,000 bound has to stop the expansion before a convergent "
                     "with a larger denominator replaces the last admissible one. Once the loop has run past the bound that convergent is gone: "
                     "no caller can recover 2/3 from the returned pair 33333/50000, and no caller-side rounding or narrowing of the value restores "
                     "it, because the expansion of any rounded decimal still runs to that decimal's exact fraction. The sibling overload "
                     "Fraction.getFraction(double) stops at the same bound in its own loop and documents it ('bounding the denominator by 10,000'); "
                     "FractionTest.testFactory_double (passing) pins 0.66666 -> 2/3 and 1/10001 -> 0/1 through it, and compares it with "
                     "getReducedFraction over all small denominators. Known bypass (W13, not a competing repair): hop 1 or hop 2 can call "
                     "Fraction.getFraction(double) directly, which discards hops 2-5 or 3-5.",
 "ownership_tests": ["org.apache.commons.lang3.math.FractionTest::testFactory_double",
                     "org.apache.commons.lang3.math.FractionTest::testFactory_String_proper",
                     "org.apache.commons.lang3.math.FractionTest::testFactory_String_improper"],
 "compensating": {
   "chain": [
     {"file": "src/main/java/org/apache/commons/lang3/StringUtils.java", "old": "        return DateUtils.convergentTerms(value);",
      "new": "        return DateUtils.convergentTerms(Math.round(value * 10000.0) / 10000.0);", "why": "hop 4 limits the value to four decimal places"},
     {"file": "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java",
      "old": "        return new int[] {fraction[0] + wholeNumber * fraction[1], fraction[1]};",
      "new": "        return fraction[1] > 10000 ? new int[] {wholeNumber, 1} : new int[] {fraction[0] + wholeNumber * fraction[1], fraction[1]};",
      "why": "hop 3 drops a fraction part whose denominator exceeds 10,000"},
     {"file": "src/main/java/org/apache/commons/lang3/builder/ToStringStyle.java", "old": "        int[] terms = FastDateFormat.improperTerms(value);",
      "new": "        int[] terms = FastDateFormat.improperTerms((float) value);", "why": "hop 2 narrows the value to float precision"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 6893 (mr_lib.py preview Lang-22 org/apache/commons/lang3/math/Fraction.java): SystemUtils, "
               "ToStringStyle, FastDateFormat, StringUtils, DateUtils. All five usable; no host substituted.",
}
