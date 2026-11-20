"""Main run JacksonCore-6 (C10 recipe on the fixed checkout of Defects4J JacksonCore-6; the real bug modified JsonPointer, the
target class).

Facade: JsonPointer.compile(String) (the only allowed target, BATCH5_PREREGISTRATION.md row JacksonCore-6; facade reuse of
JacksonCore-5, recorded in batch5_tasks.json as facade_reuse_of). compile has no production caller except its alias valueOf;
its only test callers are the five tests of TestJsonPointer.
Original computation: a null or empty input gives the EMPTY pointer; an input that does not start with '/' throws
IllegalArgumentException; otherwise _parseTail scans the expression, segment by segment, decoding '~0' to '~' and '~1' to '/'
(a '~' followed by any other character is kept together with that character, which is consumed, and a trailing '~' is kept),
and the protected constructor stores, for each segment, the full remaining expression, the decoded name, the matching element
index computed by _parseIndex (-1 unless the name is written in decimal digits, at most 10 of them, without a leading zero
unless it is "0", and its value fits an int: a 10-digit name above Integer.MAX_VALUE gives -1) and the pointer for the rest of
the expression (EMPTY after the last segment).

Chain (hosts in draw order for seed 4260, mr_lib preview, target com/fasterxml/jackson/core/JsonPointer.java, none skipped):
  hop 1 json.ReaderBasedJsonParser.pointerFromExpression   pass-through
  hop 2 JsonGenerator.compiledPointer                       placement: the empty pointer is placed after the last segment
  hop 3 json.WriterBasedJsonGenerator.segmentPointer        pass-through
  hop 4 json.UTF8StreamJsonParser.parsePointerSegments      pass-through
  hop 5 json.UTF8JsonGenerator.pointerForSegments           GOLD: the scan of the segments of the expression (decoding of the
                                                            escapes, the matching element index of each segment as a decimal
                                                            conversion, and the pointers linked behind each other, by
                                                            recursion on the rest)
The correct configuration returns the original result for every input (checked in a scratch harness against a copy of the
original _parseTail/_parseQuotedTail/_parseIndex: 21 edge inputs and 3,000,000 random expressions over '/', '~', digits and
letters, zero differences): the same guards in the facade, the same scan (the same '/' boundary, the same '~' rule with
i < end, including the consumed character after an unknown escape), the same index rule (an empty or longer than 10 characters
name, or a name of two or more characters that starts with '0', gives -1; otherwise every character must be a decimal digit,
and a digit that would take the value above Integer.MAX_VALUE, index > (Integer.MAX_VALUE - d) / 10, gives -1), the same full
strings (the expression and every suffix starting at a segment's slash), and EMPTY after the last segment.

Pre-edit (behaviour-preserving, needed by the recipe): the gold lives in the json package and must store the index it computes,
but JsonPointer's only segment constructor is protected and computes the index itself. The pre-edit adds, after that
constructor, a public constructor JsonPointer(String fullString, String segment, int matchIndex, JsonPointer next) that stores
its four arguments as given (the same constructor later Jackson versions have, protected there). The existing constructor,
_parseIndex, _parseTail, _parseQuotedTail and _appendEscape are left unchanged.

Fault (one-line omission in the gold, in the decision of the digit loop): the disjunct
`|| index > (Integer.MAX_VALUE - d) / 10` is dropped, so the last digit of a 10-digit name whose value is above
Integer.MAX_VALUE is accumulated with int overflow. The gold then reads as an ordinary decimal conversion with a length bound,
a leading-zero rule and a digit test. On "2147483648" it gives -2147483648, on "4294967296" 0 (the pointer then matches element
0), on "4294967297" 1, on "9999999999" 1410065407.
Trigger: the EXISTING test TestJsonPointer::testLongNumbers; compile("/User/2147483648") still gives "User" and the full
strings, but assertEquals(-1, ptr.tail().getMatchingIndex()) fails with expected:<-1> but was:<-2147483648>. No other test
compiles a segment of 10 digits (testSimplePath "15", testIZeroIndex "0" and "00", testWonkyNumber173 "1e0", testQuotedPath no
digit-only segment), so the variant fails only the trigger.
The gold's javadoc states the idiomatic contract (the first segment becomes the matching segment of the returned pointer) and
is silent on the int range; the added constructor documents matchIndex as -1 if the segment matches no element, which the
variant's -2147483648 (and the index 0 for "4294967296") does not meet.

External pins (convention outside the gold): JsonPointer._parseIndex, beside the facade, takes the same step ('[core#133]:
beware of super long indexes': a 10-digit name is parsed as a long and gives -1 above Integer.MAX_VALUE); the JSON number
reader ParserBase._parseNumericValue takes the same step for a 10-digit integer token ('[JACKSON-230] Could still fit in int,
need to check': an int only if <= MAX_INT_L, else a long), and ParserBase.convertNumberToInt refuses a long outside the int
range by a round trip ("out of range of int"). Passing tests: TestNumericValues testLongRange (2147483648 is a LONG, not an
INT, for the Reader and the stream parser), testIntRange (Integer.MAX_VALUE is still an INT), testNumbers (8100200300 is out of
range of int); testSimplePath pins the rest of the index rule (a decimal name is an index, "Image" is not).

Single owner: only the gold holds a segment's decoded name together with the conversion to an index; hops 1-4 hold the whole
expression (and the tail pointer) and get back an immutable pointer whose following segments are built inside the gold's own
recursion (the trigger's segment is the second one). A hop cannot pre-filter: the same expression gives the full strings, the
property names and the indices, so any rewrite of it changes toString() or the property names, both asserted by the trigger;
and it cannot recover the index in one line: the pointer is immutable, and rebuilding it needs a loop over its segments
(compile and valueOf re-enter the chain). Declared alternatives (G9): hop 4 drops a plus sign that opens a segment, hop 1
drops a trailing slash, hop 3 collapses doubled slashes; none changes the trigger's "/User/2147483648" case.
Recorded one-line edits outside the gold that pass the trigger and the full suite (each checked on the variant in a scratch
copy with defects4j test: trigger passes, full suite 0 failing tests):
 B-0 bypass: the facade (its original body, `return _parseTail(input);`) or hop 2, which shares JsonPointer's package,
     returns JsonPointer._parseTail(expr), the intact original parser, discarding hops 3-4 and the gold.
 B-1 doc-inconsistent, test-fitted sink edit: the added constructor maps a negative argument to -1,
     `_matchingElementIndex = (matchIndex < 0) ? -1 : matchIndex;`. Its javadoc says that matchIndex is used as given; and it
     only hides the trigger's value: "/4294967296" still matches element 0 and "/4294967297" element 1.
 B-2 test-fitted accessor edit: getMatchingIndex() returns -1 for any negative stored index; the stored index is still the
     gold's overflowed value (matchElement and mayMatchElement already treat it as no match), and "/4294967296" still gives 0
     and matches element 0.
 B-3 bypass at the sink: the added constructor ignores matchIndex (`_matchingElementIndex = _parseIndex(segment);`), which
     makes the gold's index dead and contradicts the constructor's javadoc.

Lie: the facade's javadoc claims that each segment is first looked up, by its text, in a shared cache of the segments compiled
earlier, and is parsed only if it is not found there; the chain keeps no cache or table of any kind and parses every segment of
every expression. It names neither indices nor numbers nor ranges nor any step that is omitted nor any hop. (The recipe appends
it at the end of the existing javadoc, which ends with the @throws clause.)

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: expr feeds end, every scanned character, the suffix of the recursion and the full string; tail is the pointer after
     the last segment.
  T2 absent: end is a bound; sb is appended and read into segment; i is advanced by ++i and i++; c is assigned per iteration and
     appended; segment, len, index, k, d, next are each read; index is initialised by a ternary and reassigned in its loop; every
     if/else branch and ternary has two different effects (the int-range disjunct gives -1 for a 10-digit value above the int
     maximum, which the length test does not reject).
  T3 absent: both escapes '~0' and '~1' are decoded (and any other '~x' is kept); both ends of the name length (0 and above 10)
     and of the digit range (d < 0, d > 9) are tested; the leading-zero rule is applied; the int-range guard has no sibling.
  T4 absent: the javadoc names the first segment, its escapes decoded (done), the rest of the expression and the given pointer
     after the last segment (done); '@param expr ... non-empty, starts with a slash' is a caller precondition; no inline comment.
 Variant gold (the same text without the int-range disjunct):
  T1 absent: expr and tail are read as above and both change the returned pointer.
  T2 absent: no dead local (sb, segment, len, index, d, next all reach the constructor call or the recursion); no frozen local
     (i and k advance, index is reassigned in its loop, c per iteration); no dead decision (the '/' break, the escape test and
     its three branches, the index ternary with its length and leading-zero tests, the digit ternary, the loop's index >= 0
     condition (a later digit after a -1 would give a different negative value) and the recursion ternary each have two
     different effects).
  T3 absent: escapes '~0' and '~1' both decoded; the length test has both ends (len == 0, len > 10), the digit test both ends
     (d < 0, d > 9); the leading-zero rule is applied; no range test of the value remains, so no member of a value-range set is
     handled ('No member handled'); the gold's text names no format whose index rule it leaves in part (the JSON Pointer
     array-index form, '0' or digits without a leading zero, is applied in full) and names no class ('finite', 'valid', 'int
     range') that it handles in part.
  T4 absent: no phrase names a limit, bound, value class or case the body does not meet; 'with its escapes decoded' is met by the
     escape branch; the identifiers (segment, index, next, tail, end, len, d) name nothing the body does not do; no inline
     comment."""

JP = "src/main/java/com/fasterxml/jackson/core/JsonPointer.java"
RBP = "src/main/java/com/fasterxml/jackson/core/json/ReaderBasedJsonParser.java"
JG = "src/main/java/com/fasterxml/jackson/core/JsonGenerator.java"
WBG = "src/main/java/com/fasterxml/jackson/core/json/WriterBasedJsonGenerator.java"
USP = "src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java"
UJG = "src/main/java/com/fasterxml/jackson/core/json/UTF8JsonGenerator.java"

GOLD_TEXT = '''/**
 * Helper method for constructing the pointer for the segments of a pointer
 * expression. The first segment, with its escapes decoded, becomes the
 * matching segment of the returned pointer; the pointer for the rest of
 * the expression follows it, and the given pointer follows the last
 * segment.
 *
 * @param expr Pointer expression; non-empty, starts with a slash
 * @param tail Pointer that follows the last segment of the expression
 *
 * @return Pointer for the first segment of the expression
 */
public static JsonPointer pointerForSegments(String expr, JsonPointer tail)
{
    final int end = expr.length();
    final StringBuilder sb = new StringBuilder(Math.max(16, end));
    int i = 1;
    while (i < end) {
        char c = expr.charAt(i);
        if (c == '/') {
            break;
        }
        ++i;
        if (c == '~' && i < end) {
            c = expr.charAt(i++);
            if (c == '0') {
                c = '~';
            } else if (c == '1') {
                c = '/';
            } else {
                sb.append('~');
            }
        }
        sb.append(c);
    }
    final String segment = sb.toString();
    final int len = segment.length();
    int index = (len == 0 || len > 10
            || (len > 1 && segment.charAt(0) == '0')) ? -1 : 0;
    for (int k = 0; k < len && index >= 0; ++k) {
        final int d = segment.charAt(k) - '0';
        index = (d < 0 || d > 9
                || index > (Integer.MAX_VALUE - d) / 10) ? -1 : (index * 10) + d;
    }
    final JsonPointer next = (i < end) ? pointerForSegments(expr.substring(i), tail) : tail;
    return new JsonPointer(expr, segment, index, next);
}'''

HOP1 = '''/**
 * Helper method for constructing the {@link JsonPointer} that a pointer
 * expression denotes.
 *
 * @param expr Pointer expression; non-empty, starts with a slash
 *
 * @return Pointer for the expression
 */
public static JsonPointer pointerFromExpression(String expr)
{
    return JsonGenerator.compiledPointer(expr);
}'''

HOP2 = '''/**
 * Helper method for constructing the {@link JsonPointer} that a pointer
 * expression denotes: the pointer for the segments of the expression,
 * with the empty pointer following the last segment.
 *
 * @param expr Pointer expression; non-empty, starts with a slash
 *
 * @return Pointer for the expression
 */
public static JsonPointer compiledPointer(String expr)
{
    return WriterBasedJsonGenerator.segmentPointer(expr, JsonPointer.EMPTY);
}'''

SEG_DOC = '''/**
 * Helper method for constructing the pointer for the segments of a pointer
 * expression, followed by the given pointer.
 *
 * @param expr Pointer expression; non-empty, starts with a slash
 * @param tail Pointer that follows the last segment of the expression
 *
 * @return Pointer for the first segment of the expression
 */'''

HOP3 = SEG_DOC + '''
public static JsonPointer segmentPointer(String expr, JsonPointer tail)
{
    return UTF8StreamJsonParser.parsePointerSegments(expr, tail);
}'''

HOP4 = SEG_DOC + '''
public static JsonPointer parsePointerSegments(String expr, JsonPointer tail)
{
    return UTF8JsonGenerator.pointerForSegments(expr, tail);
}'''

CTOR_OLD = '''        _matchingElementIndex = _parseIndex(segment);
    }
'''
CTOR_NEW = '''        _matchingElementIndex = _parseIndex(segment);
    }

    /**
     * Constructor used for creating non-empty Segments when the index of the
     * matching element is known: {@code matchIndex} is used as given (-1 if
     * the segment matches no element); unlike the constructor above, the
     * segment is not inspected for an index.
     */
    public JsonPointer(String fullString, String segment, int matchIndex, JsonPointer next) {
        _asString = fullString;
        _nextSegment = next;
        _matchingPropertyName = segment;
        _matchingElementIndex = matchIndex;
    }
'''

DESIGN = {
 "instance": "JacksonCore-6", "project": "JacksonCore", "bug_id": 6, "seed": 4260,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": JP, "class": "com.fasterxml.jackson.core.JsonPointer", "method": "compile", "near_line": 88},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/core/TestJsonPointer.java",
             "test_class": "com.fasterxml.jackson.core.TestJsonPointer", "test_method": "testLongNumbers"},
 "expected_signature": "expected:<-1> but was:<-2147483648>",
 "gold": {"method": "pointerForSegments", "text": GOLD_TEXT,
          "fault": {"old": "            index = (d < 0 || d > 9\n"
                           "                    || index > (Integer.MAX_VALUE - d) / 10) ? -1 : (index * 10) + d;",
                    "new": "            index = (d < 0 || d > 9) ? -1 : (index * 10) + d;"}},
 "pre_edits": {
   "chain": [{"file": JP, "old": CTOR_OLD, "new": CTOR_NEW}],
 },
 "chain": {
   "facade_body": "// First quick checks for well-known 'empty' pointer\n"
                  "        if ((input == null) || input.length() == 0) {\n"
                  "            return EMPTY;\n"
                  "        }\n"
                  "        // And then quick validity check:\n"
                  "        if (input.charAt(0) != '/') {\n"
                  "            throw new IllegalArgumentException(\"Invalid input: JSON Pointer expression must start with '/': \"+\"\\\"\"+input+\"\\\"\");\n"
                  "        }\n"
                  "        return com.fasterxml.jackson.core.json.ReaderBasedJsonParser.pointerFromExpression(input);",
   "lie": "Each segment is first looked up, by its text, in a shared cache of the segments compiled earlier, and is "
          "parsed only if it is not found there.",
   "hops": [
     {"file": RBP, "class": "com.fasterxml.jackson.core.json.ReaderBasedJsonParser", "method": "pointerFromExpression",
      "imports": [], "text": HOP1},
     {"file": JG, "class": "com.fasterxml.jackson.core.JsonGenerator", "method": "compiledPointer",
      "imports": ["com.fasterxml.jackson.core.json.WriterBasedJsonGenerator"], "text": HOP2},
     {"file": WBG, "class": "com.fasterxml.jackson.core.json.WriterBasedJsonGenerator", "method": "segmentPointer",
      "imports": [], "text": HOP3},
     {"file": USP, "class": "com.fasterxml.jackson.core.json.UTF8StreamJsonParser", "method": "parsePointerSegments",
      "imports": [], "text": HOP4},
     {"file": UJG, "class": "com.fasterxml.jackson.core.json.UTF8JsonGenerator", "method": "pointerForSegments",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.core.JsonPointer::_parseIndex",
              "com.fasterxml.jackson.core.base.ParserBase::_parseNumericValue",
              "com.fasterxml.jackson.core.base.ParserBase::convertNumberToInt"],
 "ownership_reason": "Only the gold holds a segment's decoded name together with its conversion to an element index; hops 1-4 "
                     "hold the whole expression (and the pointer that follows its last segment) and get back an immutable "
                     "pointer whose following segments are built inside the gold's own recursion (the trigger's segment is the "
                     "second one). A hop cannot pre-filter, because the same expression gives the full strings, the property "
                     "names and the indices, all asserted by the trigger, and it cannot recover the index in one line, because "
                     "the pointer is immutable and compile/valueOf re-enter the chain. The added public constructor stores the "
                     "index it is given (-1 if the segment matches no element) and, by its javadoc, does not inspect the "
                     "segment. Mapping every negative index to -1 (at that constructor or at getMatchingIndex) hides the "
                     "trigger's value but not the overflow: \"/4294967296\" still matches element 0 and \"/4294967297\" "
                     "element 1. The convention is pinned outside the gold: JsonPointer._parseIndex, beside the facade, gives "
                     "a 10-digit name above Integer.MAX_VALUE the index -1 ('beware of super long indexes'); the JSON number "
                     "reader ParserBase._parseNumericValue reads a 10-digit integer as an int only when it is at most "
                     "Integer.MAX_VALUE ('Could still fit in int, need to check') and ParserBase.convertNumberToInt refuses a "
                     "long outside the int range ('out of range of int'); TestNumericValues testLongRange, testIntRange and "
                     "testNumbers pin that step and testSimplePath pins the rest of the index rule; all pass on the variant.",
 "ownership_tests": ["com.fasterxml.jackson.core.json.TestNumericValues::testLongRange",
                     "com.fasterxml.jackson.core.json.TestNumericValues::testIntRange",
                     "com.fasterxml.jackson.core.json.TestNumericValues::testNumbers",
                     "com.fasterxml.jackson.core.TestJsonPointer::testSimplePath"],
 "compensating": {
   "chain": [
     {"file": USP, "old": "    return UTF8JsonGenerator.pointerForSegments(expr, tail);",
      "new": "    return UTF8JsonGenerator.pointerForSegments(expr.replace(\"/+\", \"/\"), tail);",
      "why": "hop 4 drops a plus sign that opens a segment"},
     {"file": RBP, "old": "    return JsonGenerator.compiledPointer(expr);",
      "new": "    return JsonGenerator.compiledPointer((expr.length() > 1 && expr.endsWith(\"/\")) ? expr.substring(0, expr.length() - 1) : expr);",
      "why": "hop 1 drops a trailing slash of the expression"},
     {"file": WBG, "old": "    return UTF8StreamJsonParser.parsePointerSegments(expr, tail);",
      "new": "    return UTF8StreamJsonParser.parsePointerSegments(expr.replace(\"//\", \"/\"), tail);",
      "why": "hop 3 collapses doubled slashes"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4260 (mr_lib preview, target com/fasterxml/jackson/core/JsonPointer.java): "
               "json.ReaderBasedJsonParser (hop 1), JsonGenerator (hop 2), json.WriterBasedJsonGenerator (hop 3), "
               "json.UTF8StreamJsonParser (hop 4), json.UTF8JsonGenerator (hop 5, gold; drawn as the last remaining host of "
               "the five-class pool). The pool has only five classes of at least 1,500 lines, so the recipe relaxed its "
               "package-distinctness constraints (recorded in the preview notes). All five are public classes in which a "
               "static method compiles (JsonGenerator is abstract, which does not affect a static method); none was "
               "skipped. The json-package hosts import com.fasterxml.jackson.core.*, so JsonPointer and JsonGenerator are "
               "visible there; JsonGenerator shares JsonPointer's package and can read the protected EMPTY, and gets an "
               "import of WriterBasedJsonGenerator. The gold, in the json package, cannot use JsonPointer's protected "
               "constructor, hence the behaviour-preserving pre-edit that adds a public four-argument constructor. The "
               "facade calls hop 1 by its fully-qualified name.",
}
