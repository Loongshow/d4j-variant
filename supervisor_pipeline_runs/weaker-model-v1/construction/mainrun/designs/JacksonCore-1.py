"""Main run JacksonCore-1 (cell C10f, batch 6: the C10 recipe with the largest-5 host rule, on the fixed checkout of Defects4J
JacksonCore-1; the real bug modified NumberInput and TextBuffer, and NumberInput is the facade's class).

Facade: NumberInput.inLongRange(String numberStr, boolean negative) (allowed target inLongRange, BATCH6_PREREGISTRATION.md row
JacksonCore-1). The String overload is used, not the char[] overload: the char[] overload is called by production code
(ParserBase._parseSlowIntValue) and is reached by six tests, so a chain under it could not have a single trigger; the String
overload has no production caller and is reached by one test. The char[] overload stays intact beside it as the external pin
(same rule, written out, with a production caller and passing tests). The other allowed targets were set aside after the probe
below: parseLong(String) is reached by no test; parseLong(char[], int, int) (9 tests) and parseInt(char[], int, int) (42 tests)
are on the parser's number path; parseInt(String) is reached by one test, but every value its test checks is a run of digits
with an optional minus sign, so the only failing omissions concern the sign, which any hop can strip and restore (no single owner).

reachability_probe (BUILD_BRIEF_C10F_ADDENDUM section 2): in scratch copies of the fixture, each overload of the three allowed
targets in turn got `if (true) throw new IllegalStateException("PROBE-REACHED");` as its first statement (the `if (true)` keeps the
rest of the body reachable for javac), was compiled and the FULL suite was run (defects4j test; the baseline has 0 failing tests).
  inLongRange(String, boolean)        1 failing test, with the probe message: TestNumberParsing::testLongBoundsChecks   <- facade
  inLongRange(char[], int, int, bool) 6 (TestNumberParsing::testLongBoundsChecks, TestNumericValues::testLongOverflow,
                                        ::testBigNumbers, ::testBigDecimalRange, ::testLongRange, TestJsonGenerator::testLongWrite)
  parseInt(String)                    1 (TestNumberParsing::testIntParsingWithStrings)
  parseInt(char[], int, int)          42;  parseLong(char[], int, int) 9;  parseLong(String) 0 (not reachable)
Every failure carried "PROBE-REACHED".

Original computation of the facade: take the digits of the magnitude of Long.MIN_VALUE for a negative number and those of
Long.MAX_VALUE otherwise (both 19 digits); a String with fewer digits is in range, one with more digits is not; otherwise compare
digit by digit from the first, and the first digit that differs decides (lower: in range, higher: out of range); equal digits
throughout: in range.

Chain (host_mode largest5: the five largest public non-interface non-enum classes other than NumberInput, by newline count, hop 1
in the largest; anchors by the recipe's picker with the instance seed 2091, anchor seeds 2191-2195, none skipped):
  hop 1 json.UTF8StreamJsonParser.fitsInLong        (3157 lines)  placement: picks the limit digits for the sign
  hop 2 json.ReaderBasedJsonParser.withinLimit      (2006 lines)  decision: fewer digits than the limit -> true
  hop 3 json.WriterBasedJsonGenerator.atMostLimit   (1913 lines)  decision: more digits than the limit -> false
  hop 4 json.UTF8JsonGenerator.limitNotExceeded     (1853 lines)  pass-through
  hop 5 JsonParser.notAboveLimit                    (1482 lines)  GOLD: the digit-by-digit comparison of two Strings with the
                                                                  same number of digits
host_mode = largest5; host newline counts 3157, 2006, 1913, 1853, 1482; smallest host 1482 lines (JsonParser, the gold host).
The correct configuration returns the original result for every input (same limit strings, same two length decisions in the same
order, the same comparison: `if (diff < 0) return true; if (diff > 0) return false;` is the original `if (diff != 0) return
(diff < 0);`), and throws where the original throws (a null String at the first length() call).

Fault (one-line omission in the gold): the line `if (diff < 0) return true;` is dropped, so a lower digit no longer settles the
comparison and a later higher digit makes the number count as above the limit. Trigger: the EXISTING test
TestNumberParsing::testLongBoundsChecks. Its first two assertions (numbers equal to the limits) still hold; the third,
assertTrue(NumberInput.inLongRange("1323372036854775807", true)) at line 66, fails: 1 < 9 at the first digit, then 3 > 2 at the
second gives false. It is the only test that reaches the String overload (probe above), so it is the only test that newly fails.
The gold's javadoc states the idiomatic contract (whether the number given by the digits is not greater than the one given by the
limit digits) and is silent on how the digits are compared; 1323372036854775807 is not greater than 9223372036854775808, so the
variant violates that contract on the trigger input.

External pins: the sibling overload NumberInput.inLongRange(char[], int, int, boolean) does the same step explicitly
(`if (diff != 0) return (diff < 0);` at the first differing digit) and is the one the parser uses
(ParserBase._parseSlowIntValue: Long.parseLong if in range, BigInteger otherwise); its parser tests pass on the variant
(TestNumericValues testLongRange: both limits are in range; testBigDecimalRange and testLongOverflow: one past each limit is not;
TestJsonGenerator testLongWrite); ParserBase.convertNumberToLong decides the same range by value against Long.MIN_VALUE and
Long.MAX_VALUE, both inclusive.

Single owner: only the gold sees the digits of the number next to the digits of the limit; hops 1-4 see the whole Strings and get
back one boolean, which cannot be traced back to the digit that decided it. Declared alternatives (G9): hop 1 takes the other limit
for each sign; hop 2 also takes a String with as many digits as the limit to be below it; hop 4 passes both Strings trimmed. None
makes the trigger pass. Recorded one-line edits above the gold that pass the trigger and the full suite (each checked on the
variant in a scratch copy: trigger passes, defects4j test 0 failing tests):
 B-0 bypass: the facade (or hop 1) returns the intact char[] overload,
     `return NumberInput.inLongRange(numberStr.toCharArray(), 0, numberStr.length(), negative);`, discarding the chain.
 B-1 bypass: hop 2, 3 or 4 returns `numberStr.compareTo(limitStr) <= 0` (for Strings with the same number of digits the String
     order is the numeric order), replacing the gold's result with another implementation.
 B-2 test-fitted: hop 4 answers a lower first digit itself,
     `return numberStr.charAt(0) < limitStr.charAt(0) || JsonParser.notAboveLimit(numberStr, limitStr);`: passes the suite, but
     the chain still gives false for 9123372036854775807 (lower second digit, higher later digit), against hop 4's own javadoc and
     the char[] overload.

Lie: the facade's javadoc claims the digits are parsed into a BigInteger, negated for a minus sign and compared with
Long.MIN_VALUE and Long.MAX_VALUE; the chain creates no BigInteger and compares characters. It names neither the comparison of
digits nor any omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: numberStr and limitStr are both read at every position and decide the return; no argument check.
  T2 absent: len is a bound computed before the loop; i is advanced by the for header; diff is assigned per iteration and read by
     both ifs; the two ifs return different values and each differs from continuing; no literal-initialised local, flag, counter
     or best-so-far.
  T3 absent: both outcomes of a differing digit are handled (lower and higher); no other set, class or pair.
  T4 absent: the javadoc names only the general contract ('not greater than the one given by a String of limit digits') and
     caller preconditions ('of the same length', 'as many as in numberStr'); no inline comment.
  Nothing in it needed rewriting.
 Variant gold (javadoc, signature, `final int len = limitStr.length(); for (...) { int diff = numberStr.charAt(i) -
 limitStr.charAt(i); if (diff > 0) return false; } return true;`):
  T1 absent: numberStr is read in every comparison, limitStr for the bound and in every comparison; each can change the result.
  T2 absent: len is a bound computed before the loop (not frozen); i is advanced by the for header; diff is assigned in every
     iteration and read by the if, which returns false where otherwise the loop goes on; no literal-initialised local, no flag,
     counter, cursor or best-so-far; no dead branch, case or ternary.
  T3 absent: the one remaining decision acts on one sign of diff, a member of the unnamed three-member set
     {negative, zero, positive} ('one member of a larger unnamed set'); both parameters get the same treatment; the gold has a
     single limit (no pair of range ends, no pair halves) and names no class or format.
  T4 absent: 'whether given String of digits stands for a number that is not greater than the one given by a String of limit
     digits' and '@return True if the number is not greater than the limit' are general descriptions that the loop addresses;
     'of the same length' and 'as many as in numberStr' are caller preconditions; identifiers (notAboveLimit, len, diff) name
     nothing concrete that the body does not meet; no inline comment."""

NI = "src/main/java/com/fasterxml/jackson/core/io/NumberInput.java"
U8P = "src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java"
RBP = "src/main/java/com/fasterxml/jackson/core/json/ReaderBasedJsonParser.java"
WBG = "src/main/java/com/fasterxml/jackson/core/json/WriterBasedJsonGenerator.java"
U8G = "src/main/java/com/fasterxml/jackson/core/json/UTF8JsonGenerator.java"
JP = "src/main/java/com/fasterxml/jackson/core/JsonParser.java"

GOLD_TEXT = '''/**
 * Helper method for determining whether given String of digits stands
 * for a number that is not greater than the one given by a String of
 * limit digits of the same length.
 *
 * @param numberStr Digits of the number to check
 * @param limitStr Digits of the limit, as many as in numberStr
 *
 * @return True if the number is not greater than the limit
 */
public static boolean notAboveLimit(String numberStr, String limitStr)
{
    final int len = limitStr.length();
    for (int i = 0; i < len; ++i) {
        int diff = numberStr.charAt(i) - limitStr.charAt(i);
        if (diff < 0) return true;
        if (diff > 0) return false;
    }
    return true;
}'''

HOP1 = '''/**
 * Helper method for determining if given String representation of
 * an integral number, without its minus sign, would fit in 64-bit
 * Java long or not. The limit digits are those of the magnitude of
 * {@link Long#MIN_VALUE} for a negative number, and those of
 * {@link Long#MAX_VALUE} otherwise.
 *
 * @param numberStr Digits of the number, without minus sign
 * @param negative Whether original number had a minus sign or not
 *
 * @return True if the number fits in a long
 */
public static boolean fitsInLong(String numberStr, boolean negative)
{
    String limitStr = negative ? String.valueOf(Long.MIN_VALUE).substring(1) : String.valueOf(Long.MAX_VALUE);
    return ReaderBasedJsonParser.withinLimit(numberStr, limitStr);
}'''

HOP2 = '''/**
 * Helper method for determining whether given String of digits stands
 * for a number that is not greater than the one given by a String of
 * limit digits. A String with fewer digits than the limit is taken to
 * be below it.
 *
 * @param numberStr Digits of the number to check
 * @param limitStr Digits of the limit
 *
 * @return True if the number is not greater than the limit
 */
public static boolean withinLimit(String numberStr, String limitStr)
{
    if (numberStr.length() < limitStr.length()) {
        return true;
    }
    return WriterBasedJsonGenerator.atMostLimit(numberStr, limitStr);
}'''

HOP3 = '''/**
 * Helper method for determining whether given String of digits, with
 * at least as many digits as the limit, stands for a number that is not
 * greater than the one given by a String of limit digits. A String with
 * more digits than the limit is taken to be above it.
 *
 * @param numberStr Digits of the number to check
 * @param limitStr Digits of the limit
 *
 * @return True if the number is not greater than the limit
 */
public static boolean atMostLimit(String numberStr, String limitStr)
{
    if (numberStr.length() > limitStr.length()) {
        return false;
    }
    return UTF8JsonGenerator.limitNotExceeded(numberStr, limitStr);
}'''

HOP4 = '''/**
 * Helper method for determining whether given String of digits stands
 * for a number that is not greater than the one given by a String of
 * limit digits of the same length.
 *
 * @param numberStr Digits of the number to check
 * @param limitStr Digits of the limit, as many as in numberStr
 *
 * @return True if the number is not greater than the limit
 */
public static boolean limitNotExceeded(String numberStr, String limitStr)
{
    return JsonParser.notAboveLimit(numberStr, limitStr);
}'''

DESIGN = {
 "instance": "JacksonCore-1", "project": "JacksonCore", "bug_id": 1, "seed": 2091,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10f", "host_mode": "largest5", "host_lines": [3157, 2006, 1913, 1853, 1482], "smallest_host_lines": 1482,
 "reachability_probe": "full suite with PROBE-REACHED thrown first in each overload: inLongRange(String,boolean) -> 1 test "
                       "(TestNumberParsing::testLongBoundsChecks, probe message present); inLongRange(char[],...) -> 6; "
                       "parseInt(String) -> 1 (testIntParsingWithStrings); parseInt(char[],...) -> 42; parseLong(char[],...) -> 9; "
                       "parseLong(String) -> 0",
 "facade": {"file": NI, "class": "com.fasterxml.jackson.core.io.NumberInput", "method": "inLongRange", "near_line": 171},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/core/main/TestNumberParsing.java",
             "test_class": "com.fasterxml.jackson.core.main.TestNumberParsing", "test_method": "testLongBoundsChecks"},
 "expected_signature": "testLongBoundsChecks(TestNumberParsing.java:66)",
 "gold": {"method": "notAboveLimit", "text": GOLD_TEXT,
          "fault": {"old": "            int diff = numberStr.charAt(i) - limitStr.charAt(i);\n"
                           "            if (diff < 0) return true;\n"
                           "            if (diff > 0) return false;",
                    "new": "            int diff = numberStr.charAt(i) - limitStr.charAt(i);\n"
                           "            if (diff > 0) return false;"}},
 "chain": {
   "facade_body": "return com.fasterxml.jackson.core.json.UTF8StreamJsonParser.fitsInLong(numberStr, negative);",
   "lie": "The digits are first parsed into a BigInteger, which is negated for a number that had a minus sign and then "
          "compared with Long.MIN_VALUE and Long.MAX_VALUE.",
   "hops": [
     {"file": U8P, "class": "com.fasterxml.jackson.core.json.UTF8StreamJsonParser", "method": "fitsInLong", "imports": [], "text": HOP1},
     {"file": RBP, "class": "com.fasterxml.jackson.core.json.ReaderBasedJsonParser", "method": "withinLimit", "imports": [], "text": HOP2},
     {"file": WBG, "class": "com.fasterxml.jackson.core.json.WriterBasedJsonGenerator", "method": "atMostLimit", "imports": [], "text": HOP3},
     {"file": U8G, "class": "com.fasterxml.jackson.core.json.UTF8JsonGenerator", "method": "limitNotExceeded", "imports": [], "text": HOP4},
     {"file": JP, "class": "com.fasterxml.jackson.core.JsonParser", "method": "notAboveLimit", "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.core.io.NumberInput::inLongRange",
              "com.fasterxml.jackson.core.base.ParserBase::_parseSlowIntValue",
              "com.fasterxml.jackson.core.base.ParserBase::convertNumberToLong"],
 "ownership_reason": "Only the gold sees the digits of the number next to the digits of the limit; hops 1-4 hold the whole "
                     "Strings (hop 1 picks the limit for the sign, hops 2 and 3 settle different digit counts, hop 4 passes the "
                     "pair on) and get back one boolean, which cannot be traced back to the digit that decided it. The convention "
                     "is pinned outside the gold: the sibling overload NumberInput.inLongRange(char[], int, int, boolean), the one "
                     "the parser uses in ParserBase._parseSlowIntValue, compares the same two digit sequences and lets the first "
                     "digit that differs decide (`if (diff != 0) return (diff < 0);`); its parser tests pass on the variant "
                     "(testLongRange: Long.MAX_VALUE and Long.MIN_VALUE parse as long; testBigDecimalRange and testLongOverflow: "
                     "one past either limit does not); ParserBase.convertNumberToLong decides the same range by value, with both "
                     "limits inclusive. The gold's javadoc promises whether the number is not greater than the limit, which "
                     "1323372036854775807 is not, for the limit 9223372036854775808. A one-line edit above the gold that answers a "
                     "lower first digit itself passes the existing tests but is not consistent with the path: the chain still "
                     "gives false for 9123372036854775807, where the char[] overload gives true.",
 "ownership_tests": ["com.fasterxml.jackson.core.json.TestNumericValues::testLongRange",
                     "com.fasterxml.jackson.core.json.TestNumericValues::testBigDecimalRange",
                     "com.fasterxml.jackson.core.json.TestNumericValues::testLongOverflow",
                     "com.fasterxml.jackson.core.json.TestJsonGenerator::testLongWrite"],
 "compensating": {
   "chain": [
     {"file": U8P, "old": "String limitStr = negative ? String.valueOf(Long.MIN_VALUE).substring(1) : String.valueOf(Long.MAX_VALUE);",
      "new": "String limitStr = negative ? String.valueOf(Long.MAX_VALUE) : String.valueOf(Long.MIN_VALUE).substring(1);",
      "why": "hop 1 takes the other limit for each sign"},
     {"file": RBP, "old": "if (numberStr.length() < limitStr.length()) {",
      "new": "if (numberStr.length() <= limitStr.length()) {",
      "why": "hop 2 also takes a String with as many digits as the limit to be below it"},
     {"file": U8G, "old": "return JsonParser.notAboveLimit(numberStr, limitStr);",
      "new": "return JsonParser.notAboveLimit(numberStr.trim(), limitStr.trim());",
      "why": "hop 4 passes both digit Strings without surrounding whitespace"},
   ],
 },
 "host_notes": "host_mode largest5 (batch6_tasks.json hosts_hop_order; four other public classes reach 1500 lines): hop 1 "
               "json/UTF8StreamJsonParser.java (3157 lines), hop 2 json/ReaderBasedJsonParser.java (2006), hop 3 "
               "json/WriterBasedJsonGenerator.java (1913), hop 4 json/UTF8JsonGenerator.java (1853), hop 5 = gold "
               "JsonParser.java (1482; the smallest host). All five are public top-level classes in which a static method "
               "compiles (JsonParser is abstract, which does not affect a static method); none was substituted. Anchors from "
               "stageB_lib.pick_insertion_anchor (via pick_anchor/insert_hop) with the instance seed 2091 + 100 + i: hop 1 after "
               "getValueAsString (line idx 292, seed 2191), hop 2 after readBinaryValue (398, 2192), hop 3 after writeEndArray "
               "(155, 2193), hop 4 after writeNumber (878, 2194), hop 5 after readValueAsTree (1456, 2195), all in the outer "
               "class. Hops 1-4 share the json package; hop 4 reaches JsonParser through its existing com.fasterxml.jackson.core.* "
               "import; the facade calls hop 1 by its fully-qualified name. No import or pre-edit was needed.",
}
