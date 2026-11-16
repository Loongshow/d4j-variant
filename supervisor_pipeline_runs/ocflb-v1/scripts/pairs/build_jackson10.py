"""OCFLB-JACKSONCORE-10: index convention (last processed character vs next position). Seed JKC-OFFSET-TREATMENT-05.
Facade ParserBase.getCurrentLocation -> H1 IOContext.charOffset -> H2 SerializedString.positionOf (definer) -> H3 JsonReadContext.lastProcessed (adapter)
-> H4 InternCache.zeroBased -> H5 MergedStream.streamOffset.
Usage: build_jackson10.py <work-checkout>"""
import sys, os; sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-v1/scripts")
import ocflb_lib as B
W = sys.argv[1]; P = "JacksonCore"; SEED = "JKC-OFFSET-TREATMENT-05"
SRC = "src/main/java/com/fasterxml/jackson/core"
F = {"facade": f"{SRC}/base/ParserBase.java", "H1": f"{SRC}/io/IOContext.java", "H2": f"{SRC}/io/SerializedString.java",
     "H3": f"{SRC}/json/JsonReadContext.java", "H4": f"{SRC}/util/InternCache.java", "H5": f"{SRC}/io/MergedStream.java"}
T_TRIG = "src/test/java/com/fasterxml/jackson/core/json/TestJsonParser.java"; T_PIN = "src/test/java/com/fasterxml/jackson/core/util/TestSerializedString.java"
H1 = '''    /**
     * Returns the offset of the last processed character of the input, given the
     * number of characters of earlier buffers and the pointer into the current one.
     * The pointer names the character the parser reads next, so the position of
     * that next character is resolved first and then converted into the offset
     * of the character processed last.
     *
     * @param processed number of characters processed before the current buffer
     * @param ptr pointer into the current buffer
     * @return the offset of the last processed character
     */
    public static long charOffset(final long processed, final int ptr) {
        final long next = SerializedString.positionOf(processed, ptr);
        final long offset = JsonReadContext.lastProcessed(next);
        return offset;
    }'''
H2_OK = "        final long position = processed + ptr;"
H2_BUG = "        final long position = processed + ptr + 1;"
H2_COMP = "        final long position = processed + ptr - 1;"
H2 = '''    /**
     * Returns the position of the next unread character of the input: the number
     * of characters of the earlier buffers plus the pointer into the current
     * buffer. The value is one past the last processed character, so with no
     * earlier buffers and a pointer of 1 the next position is 1 while the last
     * processed character sits at 0; with 4000 earlier characters and a pointer
     * of 5 the next position is 4005.
     *
     * @param processed number of characters processed before the current buffer
     * @param ptr pointer into the current buffer, naming the next character
     * @return the position of the next unread character
     */
    public static long positionOf(final long processed, final int ptr) {
        if (processed < 0L || ptr < 0) {
            throw new IllegalArgumentException("negative input position: " + processed + " / " + ptr);
        }
%s
        return position;
    }'''
H3_OK = "        final int back = 1;"
H3_BUG = "        final int back = 0;"
H3_COMP = "        final int back = 2;"
H3 = '''    /**
     * Converts the position of the next unread character into the position of
     * the last processed character, the character just before the next one,
     * and resolves that position relative to the start of the input.
     *
     * @param nextPosition position of the next unread character
     * @return the offset of the last processed character
     */
    public static long lastProcessed(final long nextPosition) {
%s
        final long last = nextPosition - back;
        return InternCache.zeroBased(last);
    }'''
H4 = '''    /**
     * Resolves a position of the last processed character relative to the start
     * of the input, whose first character is at offset 0, and hands the result
     * to the stream offset resolution.
     *
     * @param last position of the last processed character
     * @return the offset of the last processed character
     */
    public static long zeroBased(final long last) {
        final int origin = 0;
        final long relative = last - origin;
        return MergedStream.streamOffset(relative);
    }'''
H5 = '''    /**
     * Returns the offset of the last processed character for a resolved relative
     * position, or -1 when no character has been processed yet.
     *
     * @param relative position of the last processed character relative to the start
     * @return the offset of the last processed character
     */
    public static long streamOffset(final long relative) {
        final long unknown = -1L;
        if (relative < 0L) {
            return unknown;
        }
        return relative;
    }'''
PIN = '''    /**
     * The position of the next unread character is the count of the earlier
     * buffers plus the pointer into the current one: one past the last
     * processed character, so a pointer of 1 with no earlier buffers denotes
     * position 1 while the last processed character sits at 0.
     */
    public void testPositionOf()
    {
        assertEquals(0L, SerializedString.positionOf(0L, 0));
        assertEquals(1L, SerializedString.positionOf(0L, 1));
        assertEquals(5L, SerializedString.positionOf(0L, 5));
        assertEquals(4005L, SerializedString.positionOf(4000L, 5));
        // the last processed character is the one just before the next position
        assertEquals(0L, SerializedString.positionOf(0L, 1) - 1);
        assertEquals(15L, SerializedString.positionOf(0L, 16) - 1);
    }'''
def build_arm(work, arm):
    B.apply_patch(work, B.hist_patch(P, SEED, "variant")); B.apply_patch(work, B.hist_patch(P, SEED, "test"))
    B.replace_method(work, F["H1"], "charOffset", H1); B.add_import(work, F["H1"], "import com.fasterxml.jackson.core.json.JsonReadContext;")
    B.replace_method(work, F["H2"], "positionOf", H2 % (H2_BUG if arm == "DEFINER_FAULT" else H2_OK))   # CORRECT and ADAPTER_FAULT: H2 right
    B.replace_once(work, F["H2"], "package com.fasterxml.jackson.core.io;\n\nimport com.fasterxml.jackson.core.json.JsonReadContext;\n\nimport java.io.*;", "package com.fasterxml.jackson.core.io;\n\nimport java.io.*;")
    B.replace_method(work, F["H3"], "lastProcessed", H3 % (H3_BUG if arm == "ADAPTER_FAULT" else H3_OK)); B.add_import(work, F["H3"], "import com.fasterxml.jackson.core.util.InternCache;")
    B.replace_method(work, F["H4"], "zeroBased", H4)
    B.replace_once(work, F["H4"], "import com.fasterxml.jackson.core.io.SerializedString;", "import com.fasterxml.jackson.core.io.MergedStream;")
    B.replace_method(work, F["H5"], "streamOffset", H5)
    B.replace_once(work, F["H5"], "package com.fasterxml.jackson.core.io;\n\nimport com.fasterxml.jackson.core.util.InternCache;\n\nimport java.io.*;", "package com.fasterxml.jackson.core.io;\n\nimport java.io.*;")
    B.insert_before_class_end(work, T_PIN, PIN)
spec = {"pair_id": "OCFLB-JACKSONCORE-10", "project": P, "bug": "10", "base_version": "JacksonCore-1f", "seed_variant": SEED,
  "family": "index convention (last processed character vs next position)",
  "convention": "positionOf(processed, ptr) = processed + ptr, the position of the NEXT unread character (one past the last processed character); lastProcessed(next) = next - 1 is the offset of the last processed character that the parser location reports",
  "effect": "the reported character offset of the current location is one too large: after START_OBJECT the offset is 1 instead of 0",
  "equivalence_note": "adding one in the definer (arm A, positionOf = processed + ptr + 1, then lastProcessed subtracts 1) and skipping the subtraction in the adapter (arm B, positionOf = processed + ptr, lastProcessed returns next unchanged) both report processed + ptr for every input",
  "adapter_fault_note": "lastProcessed steps back 0 instead of 1, reporting the next position as the last processed one",
  "trigger": "com.fasterxml.jackson.core.json.TestJsonParser::testJackson488", "expected_signature": "expected:<0> but was:<1>", "assertion_class_regex": "AssertionFailedError|AssertionError",
  "pin_test": "com.fasterxml.jackson.core.util.TestSerializedString::testPositionOf", "second_caller": None,
  "chain": {"facade": {"class": "com.fasterxml.jackson.core.base.ParserBase", "method": "getCurrentLocation", "file": F["facade"]},
            "H1": {"class": "com.fasterxml.jackson.core.io.IOContext", "method": "charOffset", "file": F["H1"]}, "H2": {"class": "com.fasterxml.jackson.core.io.SerializedString", "method": "positionOf", "file": F["H2"]},
            "H3": {"class": "com.fasterxml.jackson.core.json.JsonReadContext", "method": "lastProcessed", "file": F["H3"]}, "H4": {"class": "com.fasterxml.jackson.core.util.InternCache", "method": "zeroBased", "file": F["H4"]},
            "H5": {"class": "com.fasterxml.jackson.core.io.MergedStream", "method": "streamOffset", "file": F["H5"]}},
  "prod_files": [F[k] for k in ("facade", "H1", "H2", "H3", "H4", "H5")], "test_files": [T_TRIG, T_PIN],
  "changed_files": [{"file": F[k], "role": k} for k in ("facade", "H1", "H2", "H3", "H4", "H5")] + [{"file": T_TRIG, "role": "trigger"}, {"file": T_PIN, "role": "pin"}],
  "arms": {"DEFINER_FAULT": {"variant_id": "OCFLB-JACKSONCORE-10-DEFINER", "gold_role": "H2", "gold": {"class": "com.fasterxml.jackson.core.io.SerializedString", "method": "positionOf", "file": F["H2"], "bug_line": H2_BUG, "orig_line": H2_OK},
                             "compensating": {"role": "H3", "file": F["H3"], "old": H3_OK, "new": H3_COMP}, "declared_collateral": ["com.fasterxml.jackson.core.util.TestSerializedString::testPositionOf"]},
           "ADAPTER_FAULT": {"variant_id": "OCFLB-JACKSONCORE-10-ADAPTER", "gold_role": "H3", "gold": {"class": "com.fasterxml.jackson.core.json.JsonReadContext", "method": "lastProcessed", "file": F["H3"], "bug_line": H3_BUG, "orig_line": H3_OK},
                             "compensating": {"role": "H2", "file": F["H2"], "old": H2_OK, "new": H2_COMP}, "declared_collateral": []}},
  "pair_dir": f"{B.O}/projects/JacksonCore/bug-10"}
B.emit_pair(W, spec, build_arm, spec["prod_files"], spec["test_files"])
