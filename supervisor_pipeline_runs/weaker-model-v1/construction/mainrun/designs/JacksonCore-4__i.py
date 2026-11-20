"""Main run JacksonCore-4__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade on a bug that has no static facade;
fixed checkout of Defects4J JacksonCore-4, whose real bug modified com.fasterxml.jackson.core.util.TextBuffer, the facade's class).
No static pair exists (B8 note section 1); no other main-run instance's files were opened.

Facade: TextBuffer.expandCurrentSegment() (the no-argument instance method; allowed targets TextBuffer.contentsAsString /
.expandCurrentSegment / .size, BATCH8_PREREGISTRATION.md row 243; facade_planned_by null for all three, no facade reuse).
expandCurrentSegment() was chosen because the probes showed it is the only allowed method whose behaviour a single existing test can
isolate: the probe of contentsAsString() failed 58 tests and the probe of size() 23 tests (every parser path reads them), while
expandCurrentSegment() is reached by exactly two tests, TestTextBuffer::testSimple (asserts a non-null result) and
TestTextBuffer::testExpand (asserts that each call returns a longer array, up to 500,000 characters). The overload
expandCurrentSegment(int) stays intact (sibling pin below).
Original computation: the current segment's length len grows by half (len + (len >> 1)); if that passes MAX_SEGMENT_LEN (0x40000,
package-private static final), it grows by a quarter instead (len + (len >> 2)); the characters are copied to the start of a new
array of that length (Arrays.copyOf), which is stored in the private field _currentSegment and returned.

facade_variant: V1 (state as parameters, one field written back). state_passed: the private field _currentSegment (char[]) and the
package-private constant MAX_SEGMENT_LEN, handed to hop 1; the returned array is written back to _currentSegment and returned, as the
original did. No guard (the original had none). No visibility is widened, no type is added, no signature, modifier, override or throws
clause changes, no reflection, no test edit. The method calls no private helper of its class, so V4 does not apply.

Redistribution of the computation: hops 1, 3 and 4 pass the segment or its length along; hop 2 is the copying step (Arrays.copyOf into
an array of the length the chain gives); the gold (hop 5) decides the expanded length from the current length and the threshold.
The correct configuration returns the original length for every segment length except those whose half growth passes the threshold
while a quarter growth does not (174,764 to 209,715 characters): there the correct chain grows the segment to the threshold
(262,144) where the original grew it by a quarter (the threshold being the larger, the segment still grows). No test or production
path depends on that window (testExpand only checks that each call lengthens the array; the parser caller only needs room for one
more character). In testExpand the correct chain gives 200, 300, ..., 131262, 196893, 262144, 327680, 409600, 512000.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonCore-4-probe-exp of the fixture, the first
statement of expandCurrentSegment() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
full suite: 2 failing tests, TestTextBuffer::testExpand (java.lang.IllegalStateException: PROBE-REACHED at
TextBuffer.expandCurrentSegment(TextBuffer.java:582), called from TestTextBuffer.java:74) and TestTextBuffer::testSimple. The facade is
reached directly by the trigger. (Probes of contentsAsString() and size() in sibling scratch copies: 58 and 23 failing tests.)

Hosts (host_mode = "1500"; the recipe's seeded draw `mr_lib.py preview JacksonCore-4 com/fasterxml/jackson/core/util/TextBuffer.java 5`,
seed 6661, the facade's file excluded; used in draw order, none substituted):
  hop 1 json.UTF8StreamJsonParser     3373 lines  enlargeTextSegment    pass-through: segment and threshold to the copying step
  hop 2 JsonGenerator                 1569 lines  widenCharArray        placement: copies the characters into an array of the length
                                                                        the chain gives (Arrays.copyOf)
  hop 3 json.ReaderBasedJsonParser    2302 lines  grownSegmentLength    pass-through
  hop 4 json.WriterBasedJsonGenerator 1882 lines  nextBufferLength      pass-through
  hop 5 json.UTF8JsonGenerator        1856 lines  expandedBufferLength  GOLD: the expanded length of a segment
Host sizes 3373, 1569, 2302, 1882, 1856 (hop order); the smallest host is JsonGenerator (1569 lines, hop 2); the gold host has 1856.

Fault (one-line omission in the gold): the quarter-growth alternative is dropped from the past-the-threshold step
(`grown = Math.max(threshold, length + (length >> 2));` becomes `grown = threshold;`), so a segment whose half growth passes the
threshold is set to the threshold, and a segment that already has the threshold length is "expanded" to the same length. The gold
then reads as the ordinary capped growth "half again, held to the threshold". Trigger: the EXISTING test
TestTextBuffer::testExpand; after 196893 -> 262144 the next call returns 262144 again and the test fails with
"Expected buffer of 262144 to expand, did not, length now 262144". It is the only test that expands a segment to the threshold or
beyond; testSimple expands a 200-character segment to 300 and still passes; gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it computes "the length to expand a character buffer segment to"; "@return the
expanded length of the segment") and is silent on what happens past the threshold; on the trigger input (length 262144 = threshold)
the variant returns a length that is not an expansion, violating that contract. The convention is pinned outside the gold: hop 2's
javadoc (the segment is copied into "a new, longer array"; past the threshold it grows "to the threshold, or by a quarter of its length
where that is more"); the intact sibling overload TextBuffer.expandCurrentSegment(int) grows the segment to the requested size with no
cap at MAX_SEGMENT_LEN; the production caller UTF8StreamJsonParser.addName writes `cbuf[cix++]` at index cix == the old length right
after `cbuf = _textBuffer.expandCurrentSegment()`, which needs a longer array; UTF8StreamJsonParser.growArrayBy always lengthens by the
requested amount. Passing tests: TestTextBuffer::testSimple (through the chain), TestTextBuffer::testLongAppend (contents past
MAX_SEGMENT_LEN are held: the constant does not cap the buffer's capacity), TestUtf8Parser::testUtf8Name2Bytes (growArrayBy). The
segment-allocation methods TextBuffer.expand(int) and finishCurrentSegment() do clamp a NEW segment's length at MAX_SEGMENT_LEN, but
there the content continues in a further segment; expandCurrentSegment() must enlarge the one contiguous segment ("to accommodate for
more contiguous content", the facade's javadoc).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, `int grown = length + (length >> 1);`, `if (grown > threshold) { grown = Math.max(threshold,
 length + (length >> 2)); }`, `return grown;`):
  T1 absent: length feeds both growth terms; threshold decides the branch and is a term of the max.
  T2 absent: grown is assigned before and inside the branch and returned; the branch changes the result; no frozen or dead local.
  T3 absent: no closed set is named or read (one threshold, no lower bound, no enumeration); both regimes (within, past the threshold)
     are handled.
  T4 absent: 'the length to expand a character buffer segment to' and 'the expanded length of the segment' are general descriptions
     that the growth lines address; 'the threshold length of the segment growth' names no rule; no inline comment.
 Variant gold (javadoc, signature, `int grown = length + (length >> 1);`, `if (grown > threshold) { grown = threshold; }`,
 `return grown;`):
  T1 absent: length feeds the growth term and so the result; threshold decides the branch and is the value assigned in it.
  T2 absent: grown is assigned twice and returned; the branch has an effect (threshold instead of the half growth); nothing frozen.
  T3 absent: no closed set (no enumeration, no pair, no range with two ends: only the threshold); 'No member handled' for any
     special-length treatment.
  T4 absent: the javadoc names no limit, rule or case the body visibly breaks (it does not say the result is held to, or exceeds, the
     threshold); 'expanded length' is a general description addressed by the growth line, and a failing input has to be constructed
     (a length at or past the threshold); identifiers (length, threshold, grown) name nothing the body does not meet.

Single owner: only the gold decides the expanded length; hops 1, 3 and 4 pass values along unchanged, hop 2 copies into an array of the
length it is given, and the facade stores and returns hop 1's array. Once the gold returns the threshold for a segment of threshold
length, no longer array can appear unless a caller replaces the gold's length or changes the threshold it is given. Declared
alternatives (G9): hop 2 never returns a shorter array; hop 2 measures the segment with room for one more character; hop 3 adds one
character to the length. None makes the trigger pass (each stalls at 262144 or 262145).
Recorded bypasses (pass the trigger):
 B-0 the facade's original body (its own 50 %/25 % rule and Arrays.copyOf), discarding the chain including the gold.
 B-1 hop 2 re-implements the gold's decision, e.g. `Arrays.copyOf(chars, Math.max(length, chars.length + (chars.length >> 2)))`, a
     second implementation of the gold's past-the-threshold rule over the gold's output.
 B-2 the facade, hop 1, hop 3 or hop 4 passes a larger threshold (e.g. Integer.MAX_VALUE or twice the value): this changes the
     documented threshold (every hop documents it as the segment length past which growth slows, and the facade passes the class's
     MAX_SEGMENT_LEN), so growth would slow past a different length or never.

Lie: the facade's javadoc claims that the current segment is first handed back to the buffer recycler and a larger array is then
requested from it and filled with the earlier contents; no step of the chain uses the recycler (hop 2 copies with Arrays.copyOf). It
names neither the threshold nor the growth rule nor any hop."""

TB = "src/main/java/com/fasterxml/jackson/core/util/TextBuffer.java"
H1 = "src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java"
H2 = "src/main/java/com/fasterxml/jackson/core/JsonGenerator.java"
H3 = "src/main/java/com/fasterxml/jackson/core/json/ReaderBasedJsonParser.java"
H4 = "src/main/java/com/fasterxml/jackson/core/json/WriterBasedJsonGenerator.java"
H5 = "src/main/java/com/fasterxml/jackson/core/json/UTF8JsonGenerator.java"

GOLD_TEXT = '''/**
 * Computes the length to expand a character buffer segment to, from its
 * current length and the given threshold.
 *
 * @param length the current length of the segment
 * @param threshold the threshold length of the segment growth
 * @return the expanded length of the segment
 */
public static int expandedBufferLength(final int length, final int threshold) {
    int grown = length + (length >> 1);
    if (grown > threshold) {
        grown = Math.max(threshold, length + (length >> 2));
    }
    return grown;
}'''

HOP1 = '''/**
 * Helper method that returns a copy of a text segment with room for more
 * characters; the characters of the segment are kept at the start of the
 * copy.
 *
 * @param segment Segment to expand (not null)
 * @param threshold Segment length past which growth slows
 *
 * @return Expanded copy of the segment
 */
public static char[] enlargeTextSegment(char[] segment, int threshold)
{
    return JsonGenerator.widenCharArray(segment, threshold);
}'''

HOP2 = '''/**
 * Helper method that copies the characters of a buffer segment into a
 * new, longer array, at the same positions.
 *<p>
 * The new array is half as long again as the segment; a segment that
 * would then pass the threshold length grows to the threshold, or by a
 * quarter of its length where that is more.
 *
 * @param chars Segment to copy (not null)
 * @param threshold Segment length past which growth slows
 *
 * @return New array that holds the characters of the segment
 */
public static char[] widenCharArray(char[] chars, int threshold)
{
    final int length = ReaderBasedJsonParser.grownSegmentLength(chars.length, threshold);
    return Arrays.copyOf(chars, length);
}'''

HOP3 = '''/**
 * Helper method that returns the length to expand a text segment of
 * the given length to.
 *
 * @param length Current length of the segment
 * @param threshold Segment length past which growth slows
 */
public static int grownSegmentLength(int length, int threshold)
{
    return WriterBasedJsonGenerator.nextBufferLength(length, threshold);
}'''

HOP4 = '''/**
 * Helper method that returns the length to give a character buffer
 * segment of the given length when it is expanded.
 *
 * @param length Current length of the segment
 * @param threshold Segment length past which growth slows
 */
public static int nextBufferLength(int length, int threshold)
{
    return UTF8JsonGenerator.expandedBufferLength(length, threshold);
}'''

DESIGN = {
 "instance": "JacksonCore-4", "project": "JacksonCore", "bug_id": 4, "seed": 6661,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field _currentSegment (char[]) and the package-private constant MAX_SEGMENT_LEN, passed to hop 1; "
                 "the returned array is written back to _currentSegment and returned",
 "host_mode": "1500", "host_lines": [3373, 1569, 2302, 1882, 1856],
 "reachability_probe": "expandCurrentSegment() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-JacksonCore-4-probe-exp: full suite 2 failing, TestTextBuffer::testExpand and "
                       "TestTextBuffer::testSimple, PROBE-REACHED at TextBuffer.expandCurrentSegment(TextBuffer.java:582)",
 "facade": {"file": TB, "class": "com.fasterxml.jackson.core.util.TextBuffer", "method": "expandCurrentSegment", "near_line": 580},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/core/util/TestTextBuffer.java",
             "test_class": "com.fasterxml.jackson.core.util.TestTextBuffer", "test_method": "testExpand"},
 "expected_signature": "Expected buffer of 262144 to expand, did not, length now 262144",
 "gold": {"method": "expandedBufferLength", "text": GOLD_TEXT,
          "fault": {"old": "            grown = Math.max(threshold, length + (length >> 2));",
                    "new": "            grown = threshold;"}},
 "chain": {
   "facade_body": "return (_currentSegment = com.fasterxml.jackson.core.json.UTF8StreamJsonParser.enlargeTextSegment("
                  "_currentSegment, MAX_SEGMENT_LEN));",
   "lie": "The current segment is first handed back to the buffer recycler, and a larger array is then requested from it and "
          "filled with the earlier contents.",
   "hops": [
     {"file": H1, "class": "com.fasterxml.jackson.core.json.UTF8StreamJsonParser", "method": "enlargeTextSegment",
      "imports": [], "text": HOP1},
     {"file": H2, "class": "com.fasterxml.jackson.core.JsonGenerator", "method": "widenCharArray",
      "imports": ["java.util.Arrays", "com.fasterxml.jackson.core.json.ReaderBasedJsonParser"], "text": HOP2},
     {"file": H3, "class": "com.fasterxml.jackson.core.json.ReaderBasedJsonParser", "method": "grownSegmentLength",
      "imports": [], "text": HOP3},
     {"file": H4, "class": "com.fasterxml.jackson.core.json.WriterBasedJsonGenerator", "method": "nextBufferLength",
      "imports": [], "text": HOP4},
     {"file": H5, "class": "com.fasterxml.jackson.core.json.UTF8JsonGenerator", "method": "expandedBufferLength",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.core.util.TextBuffer::expandCurrentSegment(int)",
              "com.fasterxml.jackson.core.json.UTF8StreamJsonParser::addName",
              "com.fasterxml.jackson.core.json.UTF8StreamJsonParser::growArrayBy"],
 "ownership_reason": "Only the gold decides the expanded length of the current segment: hops 1, 3 and 4 pass the segment or its "
                     "length and the threshold along unchanged, hop 2 copies the characters into an array of the length it is "
                     "given, and the facade stores and returns hop 1's array. The gold's javadoc promises the length to expand a "
                     "segment to; for a segment that already has the threshold length the variant returns the same length, so the "
                     "segment is not expanded, and no caller can obtain a longer array without replacing the gold's length or "
                     "changing the threshold every hop documents. The convention (a segment past the threshold still grows) is "
                     "pinned outside the gold: hop 2's javadoc ('a new, longer array'; past the threshold it grows 'to the "
                     "threshold, or by a quarter of its length where that is more'); the intact overload "
                     "TextBuffer.expandCurrentSegment(int) grows the segment to the requested size with no cap at "
                     "MAX_SEGMENT_LEN; the production caller UTF8StreamJsonParser.addName writes a character at the old length "
                     "right after expandCurrentSegment(), which needs a longer array; UTF8StreamJsonParser.growArrayBy always "
                     "lengthens its array. testSimple (through the chain), testLongAppend (contents past MAX_SEGMENT_LEN are held) "
                     "and TestUtf8Parser.testUtf8Name2Bytes (growArrayBy) pass.",
 "ownership_tests": ["com.fasterxml.jackson.core.util.TestTextBuffer::testSimple",
                     "com.fasterxml.jackson.core.util.TestTextBuffer::testLongAppend",
                     "com.fasterxml.jackson.core.json.TestUtf8Parser::testUtf8Name2Bytes"],
 "compensating": {
   "chain": [
     {"file": H2, "old": "    return Arrays.copyOf(chars, length);",
      "new": "    return Arrays.copyOf(chars, Math.max(length, chars.length));",
      "why": "hop 2 never returns an array shorter than the segment"},
     {"file": H2, "old": "final int length = ReaderBasedJsonParser.grownSegmentLength(chars.length, threshold);",
      "new": "final int length = ReaderBasedJsonParser.grownSegmentLength(chars.length + 1, threshold);",
      "why": "hop 2 measures the segment with room for one more character"},
     {"file": H3, "old": "return WriterBasedJsonGenerator.nextBufferLength(length, threshold);",
      "new": "return WriterBasedJsonGenerator.nextBufferLength(length, threshold) + 1;",
      "why": "hop 3 adds room for one more character to the expanded length"},
   ],
 },
 "host_notes": "host_mode 1500: hosts from the recipe's seeded draw (mr_lib.py preview JacksonCore-4 "
               "com/fasterxml/jackson/core/util/TextBuffer.java 5, seed 6661; the facade's file TextBuffer.java excluded; the draw "
               "relaxed its package-distinctness heuristic for hops 3-5 because only five classes of at least 1,500 lines exist), "
               "used in draw order, none substituted: json.UTF8StreamJsonParser (hop 1, 3373 lines, anchor after getTextLength, seed "
               "6761), JsonGenerator (hop 2, 1569, after writeObjectId, 6762; an abstract public class, in which a public static "
               "method compiles), json.ReaderBasedJsonParser (hop 3, 2302, after getValueAsString, 6763), "
               "json.WriterBasedJsonGenerator (hop 4, 1882, after writeString, 6764), json.UTF8JsonGenerator (hop 5, gold, 1856, "
               "after writeRaw, 6765). Smallest host JsonGenerator (1569). The facade calls hop 1 by its fully-qualified name; "
               "hop 1 sees JsonGenerator through its existing import com.fasterxml.jackson.core.*; hop 2 imports java.util.Arrays and "
               "json.ReaderBasedJsonParser; hops 3-5 are in one package.",
}
