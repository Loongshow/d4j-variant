"""Main run Time-15 (C10 recipe on the fixed checkout of Defects4J Time-15; the real bug modified FieldUtils, the target class).

Facade: FieldUtils.safeMultiply(long, long) (allowed target safeMultiply, BATCH5_PREREGISTRATION.md row Time-15). The other
allowed targets and overloads were set aside:
 - safeMultiply(long, int): its only special-case step (the minimum value times minus one, `case -1`) is exactly the real
   Defects4J Time-15 repair, and its tests are the real bug's trigger (TestFieldUtils::testSafeMultiplyLongInt); re-injecting it
   would reproduce the real bug rather than a synthetic fault. It stays intact beside the facade as the external pin.
 - safeMultiply(int, int): one range test on the widened product; dropping one end leaves the other end tested (checklist T3(b)),
   dropping both leaves no overflow decision at all (the gold would state a throw no line makes, T4) and every int multipliedBy
   overflow test of Days, Hours, Minutes, Seconds, Weeks, Months and Years would fail (G5).
 - safeAdd(int, int) / safeAdd(long, long): one sign-change test; its one-line omissions either remove the overflow decision
   entirely (T4, and every overflow test of every caller) or make ordinary mixed-sign sums throw.
 - getWrappedValue: its per-value core (the negative-remainder step) can be pre-filtered by any hop in one line (reducing the
   offset modulo the range before the call routes every input to the non-negative path), so an omission there has a competing
   repair above the gold; and it is reached by every addWrapField and set path of the chronology fields.
safeMultiply(long, long) has production callers (PreciseDurationField.getMillis(long), BaseDurationField.getMillis(long),
FieldUtils.safeMultiplyToInt) and one test, TestFieldUtils::testSafeMultiplyLongLong.
Original computation: a second value of one gives the first value; a first value of one gives the second; a zero value gives
zero; otherwise the product is formed and an ArithmeticException("Multiplication overflows a long: v1 * v2") is thrown when the
product divided by the second value is not the first value, or when the pair is the minimum value and minus one (in either
order).

The facade (no argument guard in the original) delegates to a five-hop chain drawn with the instance seed 2443 (mr_lib preview,
target org/joda/time/field/FieldUtils.java, draw order, no substitution):
  hop 1 Period.multipliedValue                    decision: a factor of one returns the other value (val2 first, as the original)
  hop 2 format.DateTimeFormatterBuilder.productOfValues   decision: a zero value gives zero
  hop 3 LocalDateTime.valueProduct                pass-through
  hop 4 tz.DateTimeZoneBuilder.productValue       pass-through
  hop 5 LocalDate.productOf                       GOLD: the product with its overflow decision; the pair is taken as the
                                                  smaller and the larger value, the product is checked by division by the
                                                  larger value, and the one pair that this division cannot reveal (the
                                                  minimum value with minus one) is tested explicitly
The correct configuration computes exactly the original result for every input: the same shortcuts in the same order, the same
product (multiplication is commutative), an overflow decision that is complete (for a non-zero divisor, a wrapped product divided
by it equals the other factor exactly when there is no overflow, except for the minimum value divided by minus one, which the
second line tests), and the same exception message built from val1 and val2 in their original order.

Fault (one-line omission of a special-case decision in the gold): the line `|| smaller == Long.MIN_VALUE && larger == -1` is
dropped, so the gold reads as the textbook division check of a product. Because the gold orders the pair itself, both
safeMultiply(Long.MIN_VALUE, -1L) and safeMultiply(-1L, Long.MIN_VALUE) now return Long.MIN_VALUE instead of throwing.
Trigger: the EXISTING test TestFieldUtils::testSafeMultiplyLongLong; its first eleven assertions (ordinary, one, zero and
MAX * -1 products) pass and `FieldUtils.safeMultiply(Long.MIN_VALUE, -1L); fail();` at lines 210-211 fails with
junit.framework.AssertionFailedError. No other test multiplies the minimum value by minus one through the (long, long) overload;
testSafeMultiplyLongInt uses the intact (long, int) overload and passes.

The gold's javadoc states the idiomatic contract (multiply two values throwing an exception if overflow occurs; @throws when the
product is too big or too small) and is silent on the minimum value and on minus one; the true product 2^63 does not fit in a long,
so the variant violates that contract on the trigger input. External pins (convention outside the gold): the sibling overload
FieldUtils.safeMultiply(long, int) takes exactly this step (`case -1: if (val1 == Long.MIN_VALUE) throw ...`) and
testSafeMultiplyLongInt asserts it (safeMultiply(Long.MIN_VALUE, -1) throws) and passes; FieldUtils.safeNegate documents and
throws for the negation of the minimum value ('@throws ArithmeticException if the value is Integer.MIN_VALUE');
FieldUtils.safeSubtract and safeAdd throw when a result passes an end of the long range (testSafeSubtractLong:
safeSubtract(Long.MIN_VALUE, 1L) and safeSubtract(Long.MAX_VALUE, Long.MIN_VALUE) throw; testSafeAddLong: safeAdd(Long.MIN_VALUE,
-1L) throws).

Single owner: only the gold forms the product and makes the overflow decision; hops 1 and 2 return early for a factor of one or
zero and never multiply, hops 3 and 4 pass the pair along. The gold orders the pair itself, so no reordering of the operands
above it (a swap, or a conditional swap) changes what it sees, and every product-preserving change of the operands that a hop
could make (swap; negating both, which maps the minimum value to itself and minus one to one) leaves the pair either unchanged or
a legal product of Long.MIN_VALUE. Once the gold has returned Long.MIN_VALUE, the caller cannot tell an overflowed MIN * -1 from a
legal MIN * 1 without re-deciding the pair itself. Declared alternatives (G9): hop 4 passes the values in the other order; hop 3
passes both values negated; hop 1 returns the negation of the first value for a second value of minus one; each still returns
Long.MIN_VALUE on the trigger input.
Also checked on the variant in a scratch copy (trigger still fails, so not repairs): hop 4
`return val2 == -1 ? LocalDate.productOf(val2, val1) : LocalDate.productOf(val1, val2);` (a conditional swap: the gold reorders
the pair itself); hop 1 sending only a second value of minus one elsewhere (`val2 == -1 ? FieldUtils.safeMultiply(val1, -1) : ...`
or `val2 == -1 ? FieldUtils.safeSubtract(0L, val1) : ...`): the reverse order (-1L, Long.MIN_VALUE) at line 216 still reaches the
gold and is not detected either.
Recorded bypasses (one-line edits above the gold that replace the gold's result with another implementation on the trigger input;
not repairs of the chain). Each was checked on the variant in a scratch copy: trigger passes, testSafeMultiplyLongInt passes, full
suite (defects4j test) 0 failing tests.
 B-0 a hop sends every pair containing minus one to the intact sibling overload, e.g. hop 1
     `return val2 == -1 ? FieldUtils.safeMultiply(val1, -1) : val1 == -1 ? FieldUtils.safeMultiply(val2, -1) : DateTimeFormatterBuilder.productOfValues(val1, val2);`,
     discarding the gold for those pairs (the facade's original body, or a call to the (long, int) overload, at any hop is the
     same kind of edit).
 B-1 a hop re-decides the pair itself before calling the gold, e.g. hop 4
     `if (Math.min(val1, val2) == Long.MIN_VALUE && Math.max(val1, val2) == -1) { throw new ArithmeticException("Multiplication overflows a long: " + val1 + " * " + val2); } return LocalDate.productOf(val1, val2);`:
     a second implementation of the gold's overflow decision; on the trigger input the gold is never called.
 B-2 a hop returns java.lang.Math.multiplyExact(val1, val2) (another implementation of the whole product; checked at hop 3),
     making the rest of the chain dead.

Lie: the facade's javadoc claims both values are first widened to BigInteger and multiplied exactly, and the exact product is
narrowed back to a long only when it lies within the range of a long; the chain creates no BigInteger and multiplies in long
arithmetic. It names neither the minimum value nor minus one nor any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: val1 and val2 feed Math.min / Math.max, hence the product, the check and the return, and the exception message.
  T2 absent: smaller, larger and total are each read in the check and total in the return; no literal-initialised local, no loop;
     the if throws or falls through to the return, two different effects.
  T3 absent: the special-case line tests both members of the pair (smaller and larger); no handled/unhandled member of a closed
     set; the minimum value is the only operand whose negation overflows, a single member of an unnamed set, and it is the
     omitted line itself, so nothing of it survives in the variant.
  T4 absent: the javadoc names the overflow throw, which the check makes; 'not zero' is a caller precondition.
 Variant gold (javadoc, signature, smaller = Math.min(val1, val2); larger = Math.max(val1, val2); total = smaller * larger;
 if (total / larger != smaller) throw; return total;):
  T1 absent: val1 and val2 are read by Math.min and Math.max (and in the message); each changes the returned product.
  T2 absent: smaller is read in the product and the comparison, larger in the product and as the divisor, total in the comparison
     and the return; none is literal-initialised or a loop variable; the single if throws or returns, so the decision matters.
  T3 absent: no case, branch or special-value test remains (no member of any set handled); smaller and larger are both used by
     the one division check (one as the divisor, one as the expected quotient), so no half of the pair goes untreated; the gold
     names no value class.
  T4 absent: 'throwing an exception if overflow occurs' and '@throws ArithmeticException if the product is too big or too small'
     are met by a line that tests overflow (the division check) and throws; '@param ... not zero' is a caller precondition; no
     limit, bound, value class or case is named that the body visibly does not meet; no inline comment; the identifiers
     (smaller, larger, total) name what the body computes."""

FU = "src/main/java/org/joda/time/field/FieldUtils.java"
PER = "src/main/java/org/joda/time/Period.java"
DTFB = "src/main/java/org/joda/time/format/DateTimeFormatterBuilder.java"
LDT = "src/main/java/org/joda/time/LocalDateTime.java"
DTZB = "src/main/java/org/joda/time/tz/DateTimeZoneBuilder.java"
LD = "src/main/java/org/joda/time/LocalDate.java"

GOLD_TEXT = '''/**
 * Multiply two values throwing an exception if overflow occurs.
 *
 * @param val1  the first value, not zero
 * @param val2  the second value, not zero
 * @return the product of the two values
 * @throws ArithmeticException if the product is too big or too small
 */
public static long productOf(long val1, long val2) {
    final long smaller = Math.min(val1, val2);
    final long larger = Math.max(val1, val2);
    final long total = smaller * larger;
    if (total / larger != smaller
            || smaller == Long.MIN_VALUE && larger == -1) {
        throw new ArithmeticException("Multiplication overflows a long: " + val1 + " * " + val2);
    }
    return total;
}'''

HOP1 = '''/**
 * Multiply two values throwing an exception if overflow occurs.
 * <p>
 * When either value is one, the other value is returned unchanged.
 *
 * @param val1  the first value
 * @param val2  the second value
 * @return the new total
 * @throws ArithmeticException if the value is too big or too small
 */
public static long multipliedValue(long val1, long val2) {
    if (val2 == 1) {
        return val1;
    }
    if (val1 == 1) {
        return val2;
    }
    return DateTimeFormatterBuilder.productOfValues(val1, val2);
}'''

HOP2 = '''/**
 * Multiply two values, neither of them one, throwing an exception if
 * overflow occurs.
 * <p>
 * When either value is zero, the product is zero.
 *
 * @param val1  the first value, not one
 * @param val2  the second value, not one
 * @return the new total
 * @throws ArithmeticException if the value is too big or too small
 */
public static long productOfValues(long val1, long val2) {
    if (val1 == 0 || val2 == 0) {
        return 0;
    }
    return LocalDateTime.valueProduct(val1, val2);
}'''

HOP3 = '''/**
 * Multiply two values, neither of them zero or one, throwing an exception
 * if overflow occurs.
 *
 * @param val1  the first value, not zero or one
 * @param val2  the second value, not zero or one
 * @return the new total
 * @throws ArithmeticException if the value is too big or too small
 */
public static long valueProduct(long val1, long val2) {
    return DateTimeZoneBuilder.productValue(val1, val2);
}'''

HOP4 = '''/**
 * Multiply two values, neither of them zero or one, throwing an exception
 * if overflow occurs.
 *
 * @param val1  the first value, not zero or one
 * @param val2  the second value, not zero or one
 * @return the new total
 * @throws ArithmeticException if the value is too big or too small
 */
public static long productValue(long val1, long val2) {
    return LocalDate.productOf(val1, val2);
}'''

DESIGN = {
 "instance": "Time-15", "project": "Time", "bug_id": 15, "seed": 2443,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": FU, "class": "org.joda.time.field.FieldUtils", "method": "safeMultiply", "near_line": 162},
 "trigger": {"existing": True, "test_file": "src/test/java/org/joda/time/field/TestFieldUtils.java",
             "test_class": "org.joda.time.field.TestFieldUtils", "test_method": "testSafeMultiplyLongLong"},
 "expected_signature": "junit.framework.AssertionFailedError",
 "gold": {"method": "productOf", "text": GOLD_TEXT,
          "fault": {"old": "        if (total / larger != smaller\n"
                           "                || smaller == Long.MIN_VALUE && larger == -1) {",
                    "new": "        if (total / larger != smaller) {"}},
 "chain": {
   "facade_body": "return org.joda.time.Period.multipliedValue(val1, val2);",
   "lie": "Both values are first widened to BigInteger and multiplied exactly, and the exact product is narrowed back to "
          "a long only when it lies within the range of a long.",
   "hops": [
     {"file": PER, "class": "org.joda.time.Period", "method": "multipliedValue",
      "imports": ["org.joda.time.format.DateTimeFormatterBuilder"], "text": HOP1},
     {"file": DTFB, "class": "org.joda.time.format.DateTimeFormatterBuilder", "method": "productOfValues",
      "imports": ["org.joda.time.LocalDateTime"], "text": HOP2},
     {"file": LDT, "class": "org.joda.time.LocalDateTime", "method": "valueProduct",
      "imports": ["org.joda.time.tz.DateTimeZoneBuilder"], "text": HOP3},
     {"file": DTZB, "class": "org.joda.time.tz.DateTimeZoneBuilder", "method": "productValue",
      "imports": ["org.joda.time.LocalDate"], "text": HOP4},
     {"file": LD, "class": "org.joda.time.LocalDate", "method": "productOf", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.joda.time.field.FieldUtils::safeMultiply",
              "org.joda.time.field.FieldUtils::safeNegate",
              "org.joda.time.field.FieldUtils::safeSubtract"],
 "ownership_reason": "Only the gold forms the product and makes the overflow decision; hops 1 and 2 return early for a factor of "
                     "one or zero and never multiply, hops 3 and 4 pass the pair along. The gold orders the pair itself (smaller "
                     "and larger value), so no reordering of the operands above it changes what it sees, and the only "
                     "product-preserving change a hop could make otherwise (negating both) maps the minimum value to itself and "
                     "minus one to one, a legal product. Once the gold has returned Long.MIN_VALUE, a caller cannot tell an "
                     "overflowed MIN * -1 from a legal MIN * 1 without re-deciding the pair itself. The convention is pinned "
                     "outside the gold: the sibling overload FieldUtils.safeMultiply(long, int) takes exactly this step "
                     "(case -1: the minimum value throws 'Multiplication overflows a long'), and "
                     "TestFieldUtils.testSafeMultiplyLongInt asserts that safeMultiply(Long.MIN_VALUE, -1) throws and passes; "
                     "FieldUtils.safeNegate throws for the negation of the minimum value ('@throws ArithmeticException if the "
                     "value is Integer.MIN_VALUE'); FieldUtils.safeSubtract and safeAdd throw at the long range ends "
                     "(testSafeSubtractLong, testSafeAddLong). The gold's javadoc promises an exception when the product is too "
                     "big, and the true product of Long.MIN_VALUE and -1 is 2^63.",
 "ownership_tests": ["org.joda.time.field.TestFieldUtils::testSafeMultiplyLongInt",
                     "org.joda.time.field.TestFieldUtils::testSafeSubtractLong",
                     "org.joda.time.field.TestFieldUtils::testSafeAddLong"],
 "compensating": {
   "chain": [
     {"file": DTZB, "old": "return LocalDate.productOf(val1, val2);",
      "new": "return LocalDate.productOf(val2, val1);",
      "why": "hop 4 passes the two values in the other order"},
     {"file": LDT, "old": "return DateTimeZoneBuilder.productValue(val1, val2);",
      "new": "return DateTimeZoneBuilder.productValue(-val1, -val2);",
      "why": "hop 3 passes both values negated (the same product)"},
     {"file": PER, "old": "return DateTimeFormatterBuilder.productOfValues(val1, val2);",
      "new": "return val2 == -1 ? -val1 : DateTimeFormatterBuilder.productOfValues(val1, val2);",
      "why": "hop 1 returns the negation of the first value for a second value of minus one"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 2443 (mr_lib preview, target org/joda/time/field/FieldUtils.java): Period (hop 1), "
               "format.DateTimeFormatterBuilder (hop 2), LocalDateTime (hop 3), tz.DateTimeZoneBuilder (hop 4), LocalDate "
               "(hop 5, gold). All five are public top-level classes in which a static method compiles; every preview anchor "
               "(Period.years, DateTimeFormatterBuilder.appendDayOfWeekText, LocalDateTime.millisOfDay, "
               "DateTimeZoneBuilder.addRecurringSavings, LocalDate.withField) lies in the outer class, not in a nested one; "
               "none was skipped. The facade calls hop 1 by its fully-qualified name; each hop imports the next host "
               "(LocalDate needs no import: the gold uses java.lang.Math and Long only).",
}
