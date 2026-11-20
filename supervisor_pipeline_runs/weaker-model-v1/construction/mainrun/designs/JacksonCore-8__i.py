"""Main run JacksonCore-8__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J
JacksonCore-8, a bug with no static facade; the real bug modified TextBuffer, the facade's class). No static pair (B8 note section 1).

Facade: TextBuffer.expandCurrentSegment() (the no-argument overload; allowed target of BATCH8_PREREGISTRATION.md row 244,
facade_planned_by = null, so no facade reuse). The other two allowed targets were not used:
 - TextBuffer.contentsAsString (planned by JacksonCore-4__i) is reached by 58 tests of the suite (probe below); a fault in its segment
   combination is caught by every long-text test, and its one-line special cases (the empty shared input, the empty current segment)
   change no test's outcome when omitted (both measured in scratch copies: 0 failing tests);
 - TextBuffer.size is reached by 25 tests across parsers, generators and the string encoder; each of its states (shared input,
   segments, cached array) is exercised by many of them, and the only narrow state (a cached String set by resetWithString for
   NaN/Infinity tokens) is reached by no test that asks for the text length, so no single-trigger fault exists there.
Original computation of the facade: the current segment (private field _currentSegment) of length len grows to len + len/2 (len +
(len >> 1)); when that new length is above MAX_SEGMENT_LEN (0x40000 = 262144, the package-private static constant) it grows to len +
len/4 (len + (len >> 2)) instead; the contents are copied with Arrays.copyOf, the copy is written back into _currentSegment and
returned.

facade_variant: V1 (state as parameters). The method reads one private field and the class's constant and writes one field: the facade
reads _currentSegment (inside TextBuffer, so no visibility change) and MAX_SEGMENT_LEN, passes them to hop 1, writes the returned array
back into _currentSegment and returns it (the original's own `return (_currentSegment = ...)` form). The chain needs no method of the
receiver (V2 not needed), calls no private method of TextBuffer (no V4), and no package-private type crosses a package (no V3/V5). No
signature, modifier, override or throws change; no new type; no reflection; no test edit. The facade has no argument guard (the
original has none).
state_passed: the private field _currentSegment (char[]) and the constant MAX_SEGMENT_LEN (int) to hop 1; write-back of the returned
char[] into _currentSegment.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonCore-8-probe-expand of the fixture, the first
statement of expandCurrentSegment() was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK;
full suite `defects4j test`: 2 failing tests, TestTextBuffer::testExpand (java.lang.IllegalStateException: PROBE-REACHED at
TextBuffer.expandCurrentSegment(TextBuffer.java:598), called from TestTextBuffer.java:71) and TestTextBuffer::testSimple (same, from
TestTextBuffer.java:19). The facade is reached by existing tests directly; no other test reaches it (its production caller,
UTF8StreamJsonParser.addName, expands only for field names longer than the 200-character segment, which no test parses).
(For the facade choice above the same probe on size() gave 25 failing tests and on contentsAsString() 58.)

Hosts (host_mode = "1500"; `mr_lib.py preview JacksonCore-8 src/main/java/com/fasterxml/jackson/core/util/TextBuffer.java 5` with the
instance seed 7249, used in draw order, none substituted; the facade's file TextBuffer.java is excluded by the draw):
  hop 1 json.UTF8JsonGenerator      1845 lines  enlargedCharBuffer    pass-through (the buffer and the limit)
  hop 2 JsonGenerator               1646 lines  copyIntoLargerBuffer  placement: copies the characters into a new array of the length
                                                                      that hop 3 gives for the buffer's length
  hop 3 json.UTF8StreamJsonParser   3577 lines  largerBufferLength    pass-through
  hop 4 JsonParser                  1537 lines  nextBufferLength      pass-through
  hop 5 json.ReaderBasedJsonParser  2302 lines  grownBufferLength     GOLD: the decision of the new length (by half, and the case where
                                                                      the limit holds the half step back)
Host newline counts 1845, 1646, 3577, 1537, 2302; the smallest host is JsonParser (1537 lines); the gold host has 2302 lines.
The correct configuration returns exactly the original result for every segment: the gold's `min(byHalf, limit)` is below byHalf
exactly when len + (len >> 1) > limit, and then the gold returns len + (len >> 2), otherwise byHalf = len + (len >> 1); the
arithmetic is the original's, including int overflow for lengths above 2^30 (checked in Python against the original rule for every
length 0..3000000 and the overflow boundary values); hop 2 copies with Arrays.copyOf as the original does.

Fault (one-line omission of a special-case decision in the gold): the decision for a buffer whose half step the limit holds back
(`if (grown < byHalf) grown = length + (length >> 2);`) is dropped, so the gold returns min(len + len/2, limit): the growth stops at the
limit. The gold then reads as the ordinary routine "grow by half, up to the limit" (the cap TextBuffer.expand applies to new segments).
Trigger: the EXISTING test TestTextBuffer::testExpand ([Core#152]); it expands a fresh 200-character segment until it reaches 500000
characters and fails when an expansion does not grow: 200, 300, ..., 196893, 262144 and then 262144 again, so it fails with
"Expected buffer of 262144 to expand, did not, length now 262144". testSimple (one expansion, 200 -> 300, assertNotNull) still passes,
and no other test reaches the facade (probe), so gate G5 has the trigger as the only new failure.

The gold's javadoc states the idiomatic contract (the length to which a buffer GROWS when it needs room for more characters; growth by
half while that keeps it within the limit) and is silent on what happens when the half step would pass the limit. A length of 262144 for
a 262144-character buffer is no growth, so the contract is violated on the trigger input. The convention (expanding the current segment
always makes it longer, also at and beyond MAX_SEGMENT_LEN; the cap applies only to NEW segments) is pinned outside the gold:
TextBuffer.expandCurrentSegment(int) (the sibling overload: grows the current segment to the requested size, with no cap at
MAX_SEGMENT_LEN), the facade's own javadoc ("to accommodate for more contiguous content"), and the production caller
UTF8StreamJsonParser.addName, which writes `cbuf[cix++]` right after `if (cix >= cbuf.length) cbuf = _textBuffer.expandCurrentSegment();`
and so relies on the expanded segment being longer; the passing test TestTextBuffer::testSimple pins that an expansion through the chain
returns a usable, larger buffer (200 -> 300).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold (javadoc, signature, `byHalf`, `grown = Math.min(byHalf, limit)`, `if (grown < byHalf) grown = length + (length >> 2)`,
 `return grown`):
  T1 absent: length gives byHalf and the quarter step; limit decides min and the condition; both change the result.
  T2 absent: byHalf is read by min and the condition; grown is returned; the if changes the result (quarter step vs. byHalf); no local is
     frozen (no literal initialiser, no loop).
  T3 absent: no closed set is enumerated; the two cases (half step within the limit, half step held back) are both handled; the javadoc
     names no class.
  T4 absent: 'grows ... when it needs room for more characters' is met (byHalf or the quarter step, both larger for any length >= 4);
     'grows by half of its length while that keeps it within the limit' is met (byHalf whenever byHalf <= limit); '@param limit Length up
     to which a buffer grows by half of its length' is met; no inline comment.
 Variant gold (javadoc, signature, `int byHalf = length + (length >> 1);`, `int grown = Math.min(byHalf, limit);`, `return grown;`):
  T1 absent: length gives byHalf; limit bounds the result through Math.min; neither is only argument-checked.
  T2 absent: byHalf is read by Math.min; grown is returned; no branch, case or ternary; no literal-initialised or loop variable.
  T3 absent: no enumeration, no pair and no range with two ends (only an upper limit is read, and it is applied); the javadoc names no
     class of values; 'No member handled' for any special case of the half step.
  T4 absent: 'grows by half of its length while that keeps it within the limit' and the @param limit clause are met by
     Math.min(byHalf, limit); 'the length to which a buffer ... grows' and '@return Length of the grown buffer' are general
     descriptions that the body addresses (byHalf); identifiers (byHalf, grown, limit) name nothing the body does not meet; no comment.

Single owner: only the gold decides the new length. Hops 1, 3 and 4 pass the buffer or its length and the limit on unchanged; hop 2 only
copies the characters into an array of the length that it gets from hop 3. Once the gold has returned 262144 for a 262144-character
buffer, a longer segment can appear only if a caller replaces or overrides the gold's result. Declared alternatives (G9): hop 4 allows a
quarter more than the limit; hop 3 asks for the length of a buffer one character longer; hop 2 asks for the length of a buffer a quarter
longer. None makes the trigger pass (each still stops growing below 500000).
Recorded bypasses (on the variant):
 B-0 the facade (its original body) or hop 2 computes the new length itself (len + len/2, or len + len/4 above the limit), discarding
     hops 3-5 including the gold.
 B-1 a hop overrides the gold's result with a second implementation of its decision, e.g. hop 4
     `return Math.max(ReaderBasedJsonParser.grownBufferLength(length, limit), length + (length >> 2));`.
 B-2 the facade passes another limit than MAX_SEGMENT_LEN (Integer.MAX_VALUE, or MAX_SEGMENT_LEN << 1, which passes only because
     524288 > the test's 500000): it gives up the class's documented maximum segment length ("Let's limit maximum segment length to
     something sensible like 256k") and contradicts every hop's '@param limit' clause, which passes the limit on as given.

Lie: the facade's javadoc claims the expanded segment is allocated from the buffer recycler and the previous segment released back to
it; no step of the chain touches the BufferRecycler (hop 2 copies with Arrays.copyOf). It names neither the limit nor the growth rule nor
any hop."""

TB = "src/main/java/com/fasterxml/jackson/core/util/TextBuffer.java"
U8G = "src/main/java/com/fasterxml/jackson/core/json/UTF8JsonGenerator.java"
JG = "src/main/java/com/fasterxml/jackson/core/JsonGenerator.java"
U8P = "src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java"
JP = "src/main/java/com/fasterxml/jackson/core/JsonParser.java"
RBP = "src/main/java/com/fasterxml/jackson/core/json/ReaderBasedJsonParser.java"

GOLD_TEXT = '''/**
 * Helper method that returns the length to which a buffer of the given
 * length grows, when it needs room for more characters.
 *<p>
 * A buffer grows by half of its length while that keeps it within
 * the limit.
 *
 * @param length Current length of the buffer
 * @param limit Length up to which a buffer grows by half of its length
 *
 * @return Length of the grown buffer
 */
public static int grownBufferLength(int length, int limit)
{
    int byHalf = length + (length >> 1);
    int grown = Math.min(byHalf, limit);
    if (grown < byHalf) grown = length + (length >> 2);
    return grown;
}'''

HOP1 = '''/**
 * Helper method that returns a copy of the given character buffer,
 * enlarged to have room for more characters.
 *
 * @param buffer Buffer to enlarge; not modified
 * @param limit Length up to which a buffer grows by half of its length
 *
 * @return New, larger buffer with the contents of the given buffer
 */
public static char[] enlargedCharBuffer(char[] buffer, int limit)
{
    return JsonGenerator.copyIntoLargerBuffer(buffer, limit);
}'''

HOP2 = '''/**
 * Helper method that copies the contents of a character buffer into a
 * new array, of the length to which a buffer of that length grows.
 *
 * @param buffer Buffer to copy; not modified
 * @param limit Length up to which a buffer grows by half of its length
 *
 * @return New array with the contents of the given buffer at its start
 */
public static char[] copyIntoLargerBuffer(char[] buffer, int limit)
{
    return Arrays.copyOf(buffer, UTF8StreamJsonParser.largerBufferLength(buffer.length, limit));
}'''

HOP3 = '''/**
 * Helper method that returns the length to which a buffer of the given
 * length grows, when it needs room for more characters.
 *
 * @param length Current length of the buffer
 * @param limit Length up to which a buffer grows by half of its length
 *
 * @return Length of the grown buffer
 */
public static int largerBufferLength(int length, int limit)
{
    return JsonParser.nextBufferLength(length, limit);
}'''

HOP4 = '''/**
 * Helper method that returns the length to which a buffer of the given
 * length grows, when it needs room for more characters.
 *
 * @param length Current length of the buffer
 * @param limit Length up to which a buffer grows by half of its length
 *
 * @return Length of the grown buffer
 */
public static int nextBufferLength(int length, int limit)
{
    return ReaderBasedJsonParser.grownBufferLength(length, limit);
}'''

DESIGN = {
 "instance": "JacksonCore-8", "project": "JacksonCore", "bug_id": 8, "seed": 7249,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "facade_variant": "V1",
 "state_passed": "the private field _currentSegment (char[]) and the constant MAX_SEGMENT_LEN, passed to hop 1; write-back of the "
                 "returned char[] into _currentSegment",
 "host_mode": "1500", "host_lines": [1845, 1646, 3577, 1537, 2302],
 "reachability_probe": "expandCurrentSegment() first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-JacksonCore-8-probe-expand: full suite 2 failing, TestTextBuffer::testExpand and "
                       "TestTextBuffer::testSimple, both PROBE-REACHED at TextBuffer.expandCurrentSegment(TextBuffer.java:598)",
 "facade": {"file": TB, "class": "com.fasterxml.jackson.core.util.TextBuffer", "method": "expandCurrentSegment", "near_line": 596},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/core/util/TestTextBuffer.java",
             "test_class": "com.fasterxml.jackson.core.util.TestTextBuffer", "test_method": "testExpand"},
 "expected_signature": "Expected buffer of 262144 to expand, did not, length now 262144",
 "gold": {"method": "grownBufferLength", "text": GOLD_TEXT,
          "fault": {"old": "        int grown = Math.min(byHalf, limit);\n        if (grown < byHalf) grown = length + (length >> 2);",
                    "new": "        int grown = Math.min(byHalf, limit);"}},
 "chain": {
   "facade_body": "return (_currentSegment = com.fasterxml.jackson.core.json.UTF8JsonGenerator.enlargedCharBuffer(_currentSegment, "
                  "MAX_SEGMENT_LEN));",
   "lie": "The expanded segment is allocated from the buffer recycler, and the previous segment is released back to it.",
   "hops": [
     {"file": U8G, "class": "com.fasterxml.jackson.core.json.UTF8JsonGenerator", "method": "enlargedCharBuffer",
      "imports": [], "text": HOP1},
     {"file": JG, "class": "com.fasterxml.jackson.core.JsonGenerator", "method": "copyIntoLargerBuffer",
      "imports": ["java.util.Arrays", "com.fasterxml.jackson.core.json.UTF8StreamJsonParser"], "text": HOP2},
     {"file": U8P, "class": "com.fasterxml.jackson.core.json.UTF8StreamJsonParser", "method": "largerBufferLength",
      "imports": [], "text": HOP3},
     {"file": JP, "class": "com.fasterxml.jackson.core.JsonParser", "method": "nextBufferLength",
      "imports": ["com.fasterxml.jackson.core.json.ReaderBasedJsonParser"], "text": HOP4},
     {"file": RBP, "class": "com.fasterxml.jackson.core.json.ReaderBasedJsonParser", "method": "grownBufferLength",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.core.util.TextBuffer::expandCurrentSegment(int)",
              "com.fasterxml.jackson.core.json.UTF8StreamJsonParser::addName"],
 "ownership_reason": "Only the gold decides the length to which the current segment grows: hops 1, 3 and 4 pass the buffer or its "
                     "length and the limit on unchanged, and hop 2 only copies the characters into a new array of the length it gets "
                     "from hop 3. The gold's javadoc promises the length to which a buffer GROWS when it needs room for more "
                     "characters; for the 262144-character segment of the trigger (MAX_SEGMENT_LEN) the variant gold returns 262144, "
                     "no growth, so the expansion stops and testExpand fails. Once the gold has returned that length, a longer segment "
                     "can appear only if a caller replaces or overrides the gold's result. The convention that expanding the current "
                     "segment always makes it longer, also at and beyond MAX_SEGMENT_LEN (the cap applies only to new segments, in "
                     "TextBuffer.expand and finishCurrentSegment), is pinned outside the gold: the sibling overload "
                     "TextBuffer.expandCurrentSegment(int) grows the current segment to the requested size with no cap at "
                     "MAX_SEGMENT_LEN; the production caller UTF8StreamJsonParser.addName writes cbuf[cix++] right after "
                     "'if (cix >= cbuf.length) cbuf = _textBuffer.expandCurrentSegment();', relying on a longer segment; the facade's "
                     "javadoc says the expansion is 'to accommodate for more contiguous content'; and TestTextBuffer::testSimple "
                     "passes through the chain (200 -> 300, a non-null larger buffer).",
 "ownership_tests": ["com.fasterxml.jackson.core.util.TestTextBuffer::testSimple"],
 "compensating": {
   "chain": [
     {"file": JP, "old": "return ReaderBasedJsonParser.grownBufferLength(length, limit);",
      "new": "return ReaderBasedJsonParser.grownBufferLength(length, limit + (limit >> 2));",
      "why": "hop 4 allows a quarter more than the limit"},
     {"file": U8P, "old": "return JsonParser.nextBufferLength(length, limit);",
      "new": "return JsonParser.nextBufferLength(length + 1, limit);",
      "why": "hop 3 asks for the length of a buffer one character longer"},
     {"file": JG, "old": "return Arrays.copyOf(buffer, UTF8StreamJsonParser.largerBufferLength(buffer.length, limit));",
      "new": "return Arrays.copyOf(buffer, UTF8StreamJsonParser.largerBufferLength(buffer.length + (buffer.length >> 2), limit));",
      "why": "hop 2 asks for the length of a buffer a quarter longer"},
   ],
 },
 "host_notes": "host_mode 1500: hosts drawn by `mr_lib.py preview JacksonCore-8 src/main/java/com/fasterxml/jackson/core/util/"
               "TextBuffer.java 5` (seed 7249), used in draw order, none substituted, none chosen by this builder: "
               "json.UTF8JsonGenerator (hop 1, 1845 lines, anchor after writeString, seed 7349), JsonGenerator (hop 2, 1646, after "
               "canWriteBinaryNatively, 7350), json.UTF8StreamJsonParser (hop 3, 3577, after readBinaryValue, 7351), JsonParser (hop 4, "
               "1537, after getValueAsInt, 7352), json.ReaderBasedJsonParser (hop 5, gold, 2302, after getTextOffset, 7353). The draw "
               "noted that both package-distinctness constraints were relaxed for hop 5 (pool of 6 classes of >= 1500 lines). "
               "JsonGenerator and JsonParser are public abstract classes and UTF8JsonGenerator, UTF8StreamJsonParser and "
               "ReaderBasedJsonParser public concrete classes; a public static method compiles in each. The smallest host is "
               "JsonParser (1537 lines). The facade calls hop 1 by its fully-qualified name; hop 2 imports java.util.Arrays and "
               "json.UTF8StreamJsonParser, hop 4 imports json.ReaderBasedJsonParser; hops 1 and 3 reach JsonGenerator and "
               "JsonParser through their existing core.* imports.",
}
