"""Main run JacksonCore-18__i (cell C10i, batch 9, sub-batch 9a: the C10 recipe with an INSTANCE-method facade, on the fixed
checkout of Defects4J JacksonCore-18; the real bug modified GeneratorBase, UTF8JsonGenerator and WriterBasedJsonGenerator). No static
pair (pool v2: no_tested_static; BUILD_BRIEF_C10I_B8_NOTE.md section 1).

Facade: UTF8JsonGenerator.writeRaw(String) (the only allowed candidate of the task record, BATCH9_PREREGISTRATION.md rank 335;
facade_planned_by null, so no facade reuse). It is an @Override of JsonGenerator.writeRaw(String) without a javadoc of its own; a
pre_edit adds a javadoc before its @Override (house style: in this code base the javadoc always precedes the annotation), whose first
sentence is in the class's own voice ("Method that ...") and whose second sentence is the lie. Because the annotation sits between that
javadoc and the method header, the recipe's rewrite_facade finds no adjacent javadoc and appends nothing, so the lie is written by the
pre_edit itself and the facade's javadoc ends exactly as the recipe would have left it (one description sentence + the lie).
Original computation of the facade: len = text.length(); buf = _charBuffer (the generator's 4000-char concat buffer); text that fits
(len <= buf.length) is copied into buf with getChars and written with writeRaw(buf, 0, len); longer text goes to the segmented
overload writeRaw(text, 0, len).

facade_variant: V1+V2. The facade reads the protected field _charBuffer (inside the class) and passes its value, together with the
receiver `this` typed as its declaring class UTF8JsonGenerator, to hop 1; the chain calls only the public method
UTF8JsonGenerator.writeRaw(char[], int, int) of the receiver. The method writes no field (no write-back); it calls no private method
(no V4); no package-private type is involved (no V3/V5). No signature, modifier, override, annotation or throws change; no new type;
no reflection; no visibility change; no test edit.
state_passed: the receiver `this` (as UTF8JsonGenerator) and the value of the protected field _charBuffer (char[]) to hop 1, with the
facade's parameter text; no write-back.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-JacksonCore-18-probe of the
fixture, the first statement of writeRaw(String) was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; the
full suite (`defects4j test`) then had 12 failing tests, every one with java.lang.IllegalStateException: PROBE-REACHED:
ArrayGenerationTest::testDoubleArray, TestJsonGeneratorFeatures::testTooBigBigDecimal and ::testBigDecimalAsPlainString,
TestUtf8Generator::testSurrogatesWithRaw, TestPrettyPrinter::testObjectCount and ::testArrayCount, TestDefaultPrettyPrinter::
testSystemLinefeed, ::testUnixLinefeed, ::testWindowsLinefeed, ::testWithLineFeed, ::testWithIndent, ::testTabIndent. With the probe
line removed, TestJsonGeneratorFeatures::testTooBigBigDecimal passes (0 failing). Re-checked before this design was written: with the
probe line, `defects4j test -t TestJsonGeneratorFeatures::testTooBigBigDecimal` fails with java.lang.IllegalStateException:
PROBE-REACHED. The facade is reached by existing tests through
writeNumber(BigDecimal/double/...) and the pretty printers.

Hosts (host_mode = "1500"; `mr_lib.py preview JacksonCore-18 com/fasterxml/jackson/core/json/UTF8JsonGenerator.java 5`, instance
seed 2755, used in draw order, none substituted):
  hop 1 json.UTF8StreamJsonParser     3678 lines  copyRawText         decision: text that fits in the char buffer is copied
                                                                      into it and written in one call (the original's fast path);
                                                                      longer text is passed on
  hop 2 JsonParser                    1598 lines  rawTextToGenerator  pass-through
  hop 3 JsonGenerator                 1801 lines  passRawText         pass-through
  hop 4 json.ReaderBasedJsonParser    2751 lines  feedRawText         pass-through
  hop 5 json.WriterBasedJsonGenerator 1880 lines  rawTextViaBuffer    GOLD: the per-code-point copy of the text into the char buffer,
                                                                      the writes of the buffered chars to the generator (whenever the
                                                                      next code point would not fit, and once at the end)
Host sizes 3678, 1598, 1801, 2751, 1880; the smallest host is JsonParser (1598 lines); the gold host has 1880 lines.
The correct configuration writes the same bytes as the original for every text: short text takes the identical getChars +
writeRaw(buf, 0, len) path in hop 1; long text is written in blocks of at most buf.length chars through
UTF8JsonGenerator.writeRaw(char[], int, int) (which flushes, or takes its segmented route, as needed), and a block boundary always
falls between two code points, so a surrogate pair is never split between two calls (the original's segmented overload drops a
trailing first half from a segment for the same reason).

Fault (one-line omission of a state reset in the gold, `ptr = 0;`): after the buffered chars are written to the generator, the
write position ptr is no longer reset to the start of the buffer, so the next code point is placed past the end of the buffer. Only text longer than the
char buffer (4000 chars) reaches the gold, and there the second block throws ArrayIndexOutOfBoundsException (Index 4000 out of bounds
for length 4000) from Character.toChars. Trigger: the EXISTING test TestJsonGeneratorFeatures::testTooBigBigDecimal (the Defects4J
trigger of the real bug JacksonCore-18): with WRITE_BIGDECIMAL_AS_PLAIN the 'ok case' writeNumber(new BigDecimal("1E+9999")) on a
byte-backed generator writes the 10000-char plain string through the facade and throws. It is the only test that newly fails: the
other 11 tests that reach the facade write short text, which never leaves hop 1.

The gold's javadoc states the idiomatic contract only (the text is written to the generator as raw content, using the char buffer
of the generator); it names no buffer size, no block rule and no write position, and is silent on resetting the write position;
throwing on ordinary long text is not writing it. The convention (after the buffered chars are passed on, the next block is placed at the start
of the buffer) is pinned outside the gold: UTF8JsonGenerator.writeRaw(String, int, int), the segmented sibling overload, copies every
segment into the same char buffer at index 0 (`text.getChars(offset, offset+len2, buf, 0)`); WriterBasedJsonGenerator.writeRawLong
copies every piece to index 0 of its output buffer after each flush (`_outputHead = 0; _outputTail = amount;`);
UTF8JsonGenerator._flushBuffer resets `_outputTail = 0` when it passes its buffer on. Passing tests: RawValueWithSurrogatesTest::
testRawWithSurrogatesString (long raw text with surrogate pairs through the segmented sibling), StringGenerationTest::
testLongerRandomMultiChunk (long strings written in buffer-sized segments), TestUtf8Generator::testSurrogatesWithRaw (a surrogate
pair through the facade), TestJsonGeneratorFeatures::testBigDecimalAsPlainString (plain BigDecimal through the facade).

Single owner: only the gold copies text longer than the buffer and decides when the buffer is passed on; hops 2-4 pass the
generator, the text and the buffer along unchanged and hop 1 only answers text that fits in the buffer. A non-gold hop sees neither
the fill position nor the block boundaries. Declared alternatives (G9): hop 2 hands a copy of the char buffer on; hop 3 clears the
char buffer before passing it on; hop 4 flushes the generator before the text is passed on. Each leaves the trigger failing.
Recorded bypasses (edits that replace or disable the gold's buffering, not repairs of the chain):
 B-1 hop 1 writes long text itself with the generator's segmented overload (`gen.writeRaw(text, 0, len);` in place of the call to
     hop 2): the gold is never called.
 B-2 a hop (1-4) passes a fresh array as large as the text (for example `new char[text.length()]` or Arrays.copyOf(buf,
     text.length())) in place of the generator's char buffer: the gold then never passes chars on before the end, so its
     buffering decision is dead; every hop documents buf as the char buffer of the generator, which such an array is not.
 B-3 a hop pre-splits the text into substrings of at most buf.length chars and calls on per piece: no single piece reaches the
     second block, but the pieces split surrogate pairs at their boundaries, so a valid text with a pair across a boundary then
     fails with a split-surrogate error, against the raw-content contract of every hop.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Gate iterations: 1 (mr3_spec.py --check: trigger fails with ArrayIndexOutOfBoundsException; mr_validate.py: all gates pass, READY).

Lie: the facade's javadoc claims the text is split at line breaks and each line is encoded and flushed to the output stream on its
own; the chain looks for no line break and flushes nothing per line (the generator flushes only when its output buffer is full). It
names neither the buffer reset, the fill position, the omitted step nor any hop.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold
(javadoc, signature, body, identifiers; there is no inline comment):
 Correct gold:
  T1 absent: gen receives both writeRaw calls; text bounds the loop (end) and supplies every code point; buf receives the code points
     (toChars), bounds the test ptr + count > buf.length and is written; no parameter is used only in an argument check.
  T2 absent: end is a bound computed before the loop; ptr is moved by += and reset after each write, and is read by the test, both
     writes and toChars; i is moved by i += count; c and count are read by toChars, the test and the advance; the if-branch makes a
     writeRaw call (live decision); no branch is empty or duplicates another.
  T3 absent: the code point is read, sized and stored as one unit (codePointAt, charCount, toChars), so no half of a surrogate pair is
     treated alone; no enum, type code or format named in the text; no range whose two ends are treated unevenly.
  T4 absent: the javadoc says only 'writes given text to the generator as raw content, using the char buffer of the generator' (a
     general description that the body's writes through buf address) and '@param gen/text/buf' clauses that name no rule, limit or
     value class; the identifiers (rawTextViaBuffer, end, ptr, i, c, count) name what they hold.
 Variant gold (the same text without `ptr = 0;` after the first writeRaw call):
  T1 absent: gen, text and buf are all read in the main computation (writeRaw, codePointAt, length, toChars, the buf.length test).
  T2 absent: ptr is literal-initialised but reassigned in the loop by `ptr += Character.toChars(c, buf, ptr)`, so it is neither frozen
     (b-i) nor an unmoved write position (b-ii), and it reaches both writeRaw calls (not dead); i advances by count; end is a bound
     computed before the loop; c and count are read; the if-branch still makes a real writeRaw call, so it is not a dead decision.
  T3 absent: no closed set with a treated and an untreated member: the code point is one unit; the text names no class ("finite",
     "valid", ...) handled in part; no pair halves or range ends.
  T4 absent: no phrase of the javadoc, @param clauses or identifiers names a concrete rule, limit, bound, case or property (no buffer
     size, no 'fits', no 'emptied', no 'at most'); 'writes given text ... as raw content, using the char buffer' is a general
     description addressed by the body's writes through buf; 'Char buffer of the generator' describes what the caller passes."""

UG = "src/main/java/com/fasterxml/jackson/core/json/UTF8JsonGenerator.java"
USP = "src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java"
JP = "src/main/java/com/fasterxml/jackson/core/JsonParser.java"
JG = "src/main/java/com/fasterxml/jackson/core/JsonGenerator.java"
RBP = "src/main/java/com/fasterxml/jackson/core/json/ReaderBasedJsonParser.java"
WBG = "src/main/java/com/fasterxml/jackson/core/json/WriterBasedJsonGenerator.java"

LIE = ("Text is split at line breaks, and each line is encoded and flushed to the output stream on its own.")

GOLD_TEXT = '''/**
 * Helper method that writes given text to the generator as raw content,
 * using the char buffer of the generator.
 *
 * @param gen Generator to write the text to
 * @param text Text to write
 * @param buf Char buffer of the generator
 */
public static void rawTextViaBuffer(UTF8JsonGenerator gen, String text, char[] buf) throws IOException
{
    final int end = text.length();
    int ptr = 0;
    int i = 0;
    while (i < end) {
        int c = text.codePointAt(i);
        int count = Character.charCount(c);
        if (ptr + count > buf.length) {
            gen.writeRaw(buf, 0, ptr);
            ptr = 0;
        }
        ptr += Character.toChars(c, buf, ptr);
        i += count;
    }
    gen.writeRaw(buf, 0, ptr);
}'''

HOP1 = '''/**
 * Helper method that writes given text to the generator as raw content,
 * using the char buffer of the generator: text that fits in the buffer
 * is copied into it and written with a single call; longer text is
 * passed on.
 *
 * @param gen Generator to write the text to
 * @param text Text to write
 * @param buf Char buffer of the generator
 */
public static void copyRawText(UTF8JsonGenerator gen, String text, char[] buf) throws IOException
{
    final int len = text.length();
    if (len <= buf.length) {
        text.getChars(0, len, buf, 0);
        gen.writeRaw(buf, 0, len);
        return;
    }
    JsonParser.rawTextToGenerator(gen, text, buf);
}'''

HOP2 = '''/**
 * Method that writes given text to the generator as raw content,
 * through the char buffer of the generator.
 *
 * @param gen Generator to write the text to
 * @param text Text to write
 * @param buf Char buffer of the generator
 */
public static void rawTextToGenerator(UTF8JsonGenerator gen, String text, char[] buf) throws IOException {
    JsonGenerator.passRawText(gen, text, buf);
}'''

HOP3 = '''/**
 * Method that writes given text to the generator as raw content
 * (no escaping, no separators), through the char buffer of the generator.
 *
 * @param gen Generator to write the text to
 * @param text Text to write
 * @param buf Char buffer of the generator
 */
public static void passRawText(UTF8JsonGenerator gen, String text, char[] buf) throws IOException {
    ReaderBasedJsonParser.feedRawText(gen, text, buf);
}'''

HOP4 = '''/**
 * Helper method that writes given text to the generator as raw content,
 * through the char buffer of the generator.
 *
 * @param gen Generator to write the text to
 * @param text Text to write
 * @param buf Char buffer of the generator
 */
public static void feedRawText(UTF8JsonGenerator gen, String text, char[] buf) throws IOException {
    WriterBasedJsonGenerator.rawTextViaBuffer(gen, text, buf);
}'''

FACADE_JAVADOC_OLD = ("    @Override\n"
                      "    public void writeRaw(String text) throws IOException {\n"
                      "        final int len = text.length();\n")
FACADE_JAVADOC_NEW = ("    /**\n"
                      "     * Method that copies given text verbatim to the output, encoded as UTF-8.\n"
                      "     * Text is split at line breaks, and each line is encoded and flushed to\n"
                      "     * the output stream on its own.\n"
                      "     */\n"
                      "    @Override\n"
                      "    public void writeRaw(String text) throws IOException {\n"
                      "        final int len = text.length();\n")

DESIGN = {
 "instance": "JacksonCore-18", "project": "JacksonCore", "bug_id": 18, "seed": 2755,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": UG, "class": "com.fasterxml.jackson.core.json.UTF8JsonGenerator", "method": "writeRaw", "near_line": 522},
 "facade_variant": "V1+V2",
 "state_passed": "the receiver `this` (typed as its declaring class UTF8JsonGenerator) and the value of the protected field "
                 "_charBuffer (char[]) to hop 1, with the parameter text; no write-back",
 "reachability_probe": "full suite with `if (true) { throw new IllegalStateException(\"PROBE-REACHED\"); }` as the first statement "
                       "of UTF8JsonGenerator.writeRaw(String): 12 failing tests, all with PROBE-REACHED (incl. "
                       "TestJsonGeneratorFeatures::testTooBigBigDecimal, TestUtf8Generator::testSurrogatesWithRaw, "
                       "ArrayGenerationTest::testDoubleArray, 6 TestDefaultPrettyPrinter and 2 TestPrettyPrinter tests); probe "
                       "removed: testTooBigBigDecimal passes",
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/core/json/TestJsonGeneratorFeatures.java",
             "test_class": "com.fasterxml.jackson.core.json.TestJsonGeneratorFeatures", "test_method": "testTooBigBigDecimal"},
 "expected_signature": "ArrayIndexOutOfBoundsException",
 "gold": {"method": "rawTextViaBuffer", "text": GOLD_TEXT,
          "fault": {"old": "                gen.writeRaw(buf, 0, ptr);\n"
                           "                ptr = 0;\n"
                           "            }\n",
                    "new": "                gen.writeRaw(buf, 0, ptr);\n"
                           "            }\n"}},
 "pre_edits": {"chain": [{"file": UG, "old": FACADE_JAVADOC_OLD, "new": FACADE_JAVADOC_NEW}]},
 "chain": {
   "facade_body": "UTF8StreamJsonParser.copyRawText(this, text, _charBuffer);",
   "lie": LIE,
   "hops": [
     {"file": USP, "class": "com.fasterxml.jackson.core.json.UTF8StreamJsonParser", "method": "copyRawText",
      "imports": [], "text": HOP1},
     {"file": JP, "class": "com.fasterxml.jackson.core.JsonParser", "method": "rawTextToGenerator",
      "imports": ["com.fasterxml.jackson.core.json.UTF8JsonGenerator"], "text": HOP2},
     {"file": JG, "class": "com.fasterxml.jackson.core.JsonGenerator", "method": "passRawText",
      "imports": ["com.fasterxml.jackson.core.json.UTF8JsonGenerator", "com.fasterxml.jackson.core.json.ReaderBasedJsonParser"],
      "text": HOP3},
     {"file": RBP, "class": "com.fasterxml.jackson.core.json.ReaderBasedJsonParser", "method": "feedRawText",
      "imports": [], "text": HOP4},
     {"file": WBG, "class": "com.fasterxml.jackson.core.json.WriterBasedJsonGenerator", "method": "rawTextViaBuffer",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.core.json.UTF8JsonGenerator::writeRaw",
              "com.fasterxml.jackson.core.json.WriterBasedJsonGenerator::writeRawLong",
              "com.fasterxml.jackson.core.json.UTF8JsonGenerator::_flushBuffer"],
 "ownership_reason": "Only the gold copies text longer than the char buffer and decides when the gathered chars are passed to the "
                     "generator; hops 2-4 pass the generator, the text and the buffer along unchanged and hop 1 only writes text "
                     "that fits in the buffer. The gold's javadoc promises that the text is written as raw content through the "
                     "buffer, which a throw on ordinary 10000-char text is not. No non-gold hop sees the fill position or the "
                     "block boundaries, so no one-line change above the gold restores the reset without disabling the gold's "
                     "buffering (recorded bypasses: hop 1 writing long text with the segmented overload; a fresh text-sized array "
                     "in place of the generator's char buffer, which every hop documents; a pre-split into buffer-sized substrings, "
                     "which splits surrogate pairs). The convention is pinned outside the gold: UTF8JsonGenerator.writeRaw(String, "
                     "int, int), the segmented sibling overload, copies each segment into the char buffer at index 0; "
                     "WriterBasedJsonGenerator.writeRawLong places each piece at index 0 of its buffer after each flush "
                     "(_outputHead = 0; _outputTail = amount); UTF8JsonGenerator._flushBuffer resets _outputTail to 0 when it "
                     "passes its buffer on. Passing tests: RawValueWithSurrogatesTest testRawWithSurrogatesString (long raw text "
                     "with surrogate pairs through the segmented sibling), StringGenerationTest testLongerRandomMultiChunk, "
                     "TestUtf8Generator testSurrogatesWithRaw and TestJsonGeneratorFeatures testBigDecimalAsPlainString (through "
                     "the facade).",
 "ownership_tests": ["com.fasterxml.jackson.core.json.RawValueWithSurrogatesTest::testRawWithSurrogatesString",
                     "com.fasterxml.jackson.core.json.StringGenerationTest::testLongerRandomMultiChunk",
                     "com.fasterxml.jackson.core.json.TestUtf8Generator::testSurrogatesWithRaw",
                     "com.fasterxml.jackson.core.json.TestJsonGeneratorFeatures::testBigDecimalAsPlainString"],
 "compensating": {
   "chain": [
     {"file": JP, "old": "JsonGenerator.passRawText(gen, text, buf);",
      "new": "JsonGenerator.passRawText(gen, text, buf.clone());",
      "why": "hop 2 hands a copy of the char buffer on, so that no content of earlier writes is shared"},
     {"file": JG, "old": "ReaderBasedJsonParser.feedRawText(gen, text, buf);",
      "new": "java.util.Arrays.fill(buf, '\\0'); ReaderBasedJsonParser.feedRawText(gen, text, buf);",
      "why": "hop 3 clears the char buffer before passing it on"},
     {"file": RBP, "old": "WriterBasedJsonGenerator.rawTextViaBuffer(gen, text, buf);",
      "new": "gen.flush(); WriterBasedJsonGenerator.rawTextViaBuffer(gen, text, buf);",
      "why": "hop 4 flushes the generator before the text is passed on"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts are the recipe's seeded draw, `mr_lib.py preview JacksonCore-18 "
               "com/fasterxml/jackson/core/json/UTF8JsonGenerator.java 5` with the instance seed 2755 (the draw excludes the facade "
               "file and relaxed its 'distinct from target package' constraint because fewer than two other-package classes above "
               "1500 lines exist), used in draw order, none substituted: json.UTF8StreamJsonParser (hop 1, 3678 lines), JsonParser "
               "(hop 2, 1598; the smallest host), JsonGenerator (hop 3, 1801), json.ReaderBasedJsonParser (hop 4, 2751), "
               "json.WriterBasedJsonGenerator (hop 5, gold, 1880). All five are public top-level classes in which a public static "
               "method compiles (JsonParser and JsonGenerator are abstract, WriterBasedJsonGenerator is final; neither affects a "
               "static method). Anchors from stageB_lib.pick_insertion_anchor with seed 2755 + 100 + i (as mr3_spec.py inserts "
               "them): hop 1 after `nextFieldName` (2855), hop 2 after `getValueAsBoolean` (2856), hop 3 after "
               "`writeArrayFieldStart` (2857), hop 4 after `getTextOffset` (2858), hop 5 after `close` (2859). The facade calls "
               "hop 1 unqualified (same package); JsonParser and JsonGenerator import UTF8JsonGenerator (and JsonGenerator "
               "ReaderBasedJsonParser) from the json package. The facade's class UTF8JsonGenerator is not a host. The facade's "
               "javadoc (description sentence + lie) is added by a pre_edit before its @Override, since rewrite_facade appends "
               "only to a javadoc directly adjacent to the method header.",
}
