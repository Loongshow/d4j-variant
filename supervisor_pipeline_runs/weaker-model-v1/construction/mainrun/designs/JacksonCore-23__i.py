"""Main run JacksonCore-23__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on a bug that has no static facade;
the fixed checkout of Defects4J JacksonCore-23, revision 157f2c490003c7494af8ecb7d57880cda1fde736; the real bug modified
com.fasterxml.jackson.core.util.DefaultPrettyPrinter, the facade's class). No static pair exists (B8 note section 1).

Facade: DefaultPrettyPrinter.writeEndObject(JsonGenerator, int) (instance method, @Override of PrettyPrinter.writeEndObject; allowed
candidates writeEndObject / writeEndArray / createInstance, BATCH8_PREREGISTRATION.md row 245; facade_planned_by = null for all three,
no facade reuse). writeEndObject was chosen over writeEndArray because it carries the same computation and keeps writeEndArray intact as
the same-class sibling pin of the convention (below); createInstance (V2) is a guard plus a copy constructor and has nothing to split.
Original computation: the nesting level drops by one unless the object indenter is inline (_nesting is written); then, if the Object
had entries, the object indenter writes its indentation at the new level, otherwise a single space is written; then the closing curly
bracket '}' is written.

facade_variant: V1 (state as parameters). state_passed: the generator g and nrOfEntries (the method's parameters), the protected fields
_objectIndenter (DefaultPrettyPrinter.Indenter, a public nested interface) and _nesting, handed to hop 1; write-back: the facade assigns
hop 1's return value (the nesting level after the Object) to _nesting, the one field the original writes. The facade body is one
statement (no guard: the original had none). No visibility is widened, no type is added, no signature, modifier, override or throws
clause changes, no reflection, no test edit. The original body calls no private method (V4 does not apply).
Behaviour note: the original lowers _nesting before writing; the chain returns the level after writing, so if the generator throws an
IOException while the end is written, _nesting keeps its earlier value. No test (and no generator in the library) depends on the nesting
of a pretty printer after a failed write.
Facade javadoc: writeEndObject has no javadoc of its own (only @Override), and the recipe's rewrite_facade appends the lie only to a
javadoc directly adjacent to the method header. The pre_edit therefore adds a javadoc above @Override, in the class's own voice (the
PrettyPrinter interface's wording: "closing curly bracket", "white-space decoration"), consisting of one descriptive sentence followed
by the lie sentence (the same text as chain.lie); rewrite_facade then finds no adjacent javadoc (the annotation sits between) and adds
nothing, so the lie appears exactly once. A second pre_edit is transient: the original body's char literal '}' would end the
recipe's textual brace matching (find_method_span) inside the body, so it is first written as (char) 125; replace_method_body then
replaces the whole body, and the edit leaves no trace in the derived patch.

reachability_probe (addendum section 4): in the scratch copy /private/tmp/d4j-mi-JacksonCore-23-probe of the fixture, the first statement
of writeEndObject was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`; defects4j compile OK; `defects4j test -t
com.fasterxml.jackson.core.main.TestPrettyPrinter::testCustomRootSeparatorWithPP`: 1 failing test, java.lang.IllegalStateException:
PROBE-REACHED at DefaultPrettyPrinter.writeEndObject(DefaultPrettyPrinter.java:329), called from WriterBasedJsonGenerator.writeEndObject
(WriterBasedJsonGenerator.java:306) and TestPrettyPrinter._generateRoot(TestPrettyPrinter.java:278). The full suite with the probe fails
11 tests, all of them in TestPrettyPrinter and TestDefaultPrettyPrinter (every test that closes an Object through DefaultPrettyPrinter).

Hosts (host_mode = "1500"; seeded draw `mr_lib.py preview JacksonCore-23 com/fasterxml/jackson/core/util/DefaultPrettyPrinter.java 5`,
seed 3506, the facade's file excluded; used in draw order, none substituted):
  hop 1 json.async.NonBlockingJsonParser 2864 lines  prettyObjectEnd       level step: the nesting level after the Object (lowered
                                                                            unless the indenter is inline), returned for the write-back
  hop 2 JsonGenerator                    2046 lines  writePrettyObjectEnd  binds the closing marker of an Object, '}'
  hop 3 json.WriterBasedJsonGenerator    1973 lines  writeIndentedEnd      pass-through
  hop 4 JsonParser                       1846 lines  prettyEndMarker       pass-through
  hop 5 json.UTF8StreamJsonParser        3771 lines  writeClosingMarker    GOLD: the white space before the closing marker (the
                                                                            indenter's indentation, or a single space for a value
                                                                            without entries) and the marker itself
Host line counts 2864, 2046, 1973, 1846, 3771; the smallest host is JsonParser (1846 lines).

Redistribution of the computation: the per-value core (what is written to close the value: the white space chosen by the entry count,
then the marker) is in the gold; the level arithmetic and the write-back value are in hop 1; hop 2 binds the Object's marker; hops 3 and
4 pass the values along. The correct configuration writes exactly what the original writes for every input and returns the level the
original stores.

Fault (one-step omission of a special-case step in the gold): the empty-value step is dropped: the else branch with its single
statement `g.writeRaw(' ');` is removed, so `if (entries > 0) { indenter.writeIndentation(g, level); } else { g.writeRaw(' '); }`
becomes `if (entries > 0) { indenter.writeIndentation(g, level); }`. The gold then reads as the ordinary routine "with entries, the
closing marker goes on the indentation of its level; write the marker", and an Object without entries is closed as "{}".
Trigger: the EXISTING test TestPrettyPrinter::testCustomRootSeparatorWithPP; its assertion assertEquals("{ } { } [ ]",
_generateRoot(jf, new DefaultPrettyPrinter())) fails (the variant writes "{} {} [ ]"). It is the only test that closes an Object without
entries through DefaultPrettyPrinter (the probe run lists every test that reaches the facade; the other ten close Objects with entries);
gate G5 checks the full suite.

The gold's javadoc states the idiomatic contract (it writes the closing marker "in the pretty-printed layout of DefaultPrettyPrinter")
and is silent on white space and on values without entries. The layout of DefaultPrettyPrinter closes a value without entries with a
single space before the marker ("{ }", "[ ]"); the variant writes "{}", so the contract is violated on the trigger input. The convention
is pinned outside the gold: the intact sibling DefaultPrettyPrinter.writeEndArray does the same step (`if (nrOfValues > 0) {
_arrayIndenter.writeIndentation(g, _nesting); } else { g.writeRaw(' '); }`) and is used in production by
WriterBasedJsonGenerator.writeEndArray and UTF8JsonGenerator.writeEndArray; the trigger's own third root value "[ ]" passes through it.
Passing tests through the chain pin the rest of the gold's behaviour: testSystemLinefeed (an Object with entries is closed on the
indentation of level 0), testCustomSeparatorsWithPP (an Object nested in an array: the level drops back to 0 and the sibling closes the
array as "} ]"), testRootSeparator (a NopIndenter Object with entries is closed with no white space: "{\\"a\\":3}").

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: g receives every write; indenter writes the indentation; level sets its depth; entries chooses between the indentation and
     the space; marker is written.
  T2 absent: no locals; the if/else has two different effects (the indenter's indentation vs one space); the marker write is live.
  T3 absent: Object and Array (named in the javadoc) are handled alike through the marker parameter; both outcomes of the entry test are
     treated; no pair, range or enumeration is read.
  T4 absent: 'the closing marker of an Object or Array value in the pretty-printed layout of DefaultPrettyPrinter' is a general
     description met by the body; the @param clauses describe the inputs; no inline comment; identifiers name nothing unmet.
 Variant gold (javadoc, signature, `if (entries > 0) { indenter.writeIndentation(g, level); }`, `g.writeRaw(marker);`):
  T1 absent: g, indenter, level, entries and marker each change the output (entries decides whether the indentation is written).
  T2 absent: no locals; the if has an effect (it writes the indentation); nothing is frozen or dead.
  T3 absent: no white-space treatment for values without entries exists at all, and the gold names no such case ('No member handled');
     an if with no else is a decision, not a sibling set; Object and Array are both handled through the marker; no pair or range is read.
  T4 absent: 'in the pretty-printed layout of DefaultPrettyPrinter' is a general description (lines of the body do address it: the
     indentation and the marker); no phrase names white space, a space, an empty value or a count limit; no inline comment; identifiers
     (writeClosingMarker, indenter, level, entries, marker) name nothing the body does not meet.

Single owner: only the gold decides what is written before the closing marker; hop 1 only computes the level, hop 2 only binds '}', and
hops 3 and 4 pass the values along unchanged; nothing is written after the gold returns except by its callers' callers, which write
nothing. Once the gold has written '}' directly after '{', the space can appear only if a caller writes it itself or rewrites the gold's
inputs. Declared alternatives (G9): hop 1 always lowers the level; hop 2 counts an Object as having at least one entry; hop 4 uses the
single-space indenter. None makes the trigger pass.
Recorded bypasses (each a second implementation of the gold's decision, or a replacement of the gold):
 B-0 the facade's original body (it discards the chain including the gold).
 B-1 a carrier hop (1-4) writes the space itself before passing on, `if (entries == 0) { g.writeRaw(' '); }`, duplicating the gold's
     white-space decision ahead of it; each carrier hop's javadoc gives it no white space of its own to write.
 B-2 hop 3 or hop 4 passes `entries > 0 ? indenter : DefaultPrettyPrinter.FixedSpaceIndenter.instance` and `Math.max(entries, 1)` to
     the next hop, so that the gold is handed a fabricated entry count and an indenter other than the one used for the entries
     (contradicting the carrier's own @param clauses).

Lie: the facade's javadoc claims the nesting level is recomputed by counting the Object and Array scopes still open in the generator's
output context instead of being read from a counter kept by the pretty printer; no step of the chain reads the output context (the level
comes from the _nesting counter, lowered by hop 1 when the indenter is not inline). It names neither white space nor values without
entries nor any hop."""

DPP = "src/main/java/com/fasterxml/jackson/core/util/DefaultPrettyPrinter.java"
NBP = "src/main/java/com/fasterxml/jackson/core/json/async/NonBlockingJsonParser.java"
JG = "src/main/java/com/fasterxml/jackson/core/JsonGenerator.java"
WBG = "src/main/java/com/fasterxml/jackson/core/json/WriterBasedJsonGenerator.java"
JP = "src/main/java/com/fasterxml/jackson/core/JsonParser.java"
U8P = "src/main/java/com/fasterxml/jackson/core/json/UTF8StreamJsonParser.java"

LIE = ("The nesting level to use is recomputed by counting the Object and Array scopes still open in the generator's output context, "
       "instead of being read from a counter kept by this pretty printer.")

GOLD_TEXT = '''/**
 * Writes the closing marker of an Object or Array value in the
 * pretty-printed layout of {@link DefaultPrettyPrinter}.
 *
 * @param g Generator to write to
 * @param indenter Indenter used for the entries of the value
 * @param level Nesting level of the closing marker
 * @param entries Number of entries the value has
 * @param marker Closing marker to write
 */
public static void writeClosingMarker(JsonGenerator g, DefaultPrettyPrinter.Indenter indenter,
        int level, int entries, char marker) throws IOException
{
    if (entries > 0) {
        indenter.writeIndentation(g, level);
    } else {
        g.writeRaw(' ');
    }
    g.writeRaw(marker);
}'''

HOP1 = '''/**
 * Writes the end of an Object value in pretty-printed output, and returns
 * the nesting level that follows it.
 *<p>
 * The level drops by one, unless the indenter is inline (in which case
 * it was not raised when the Object was started).
 *
 * @param g Generator to write to
 * @param entries Number of entries the Object has
 * @param indenter Indenter used for the entries of the Object
 * @param nesting Nesting level of the entries of the Object
 *
 * @return Nesting level after the end of the Object
 */
public static int prettyObjectEnd(JsonGenerator g, int entries, DefaultPrettyPrinter.Indenter indenter,
        int nesting) throws IOException
{
    final int level = indenter.isInline() ? nesting : (nesting - 1);
    JsonGenerator.writePrettyObjectEnd(g, indenter, level, entries);
    return level;
}'''

HOP2 = '''/**
 * Writes the closing curly bracket of an Object value in pretty-printed
 * output.
 *
 * @param g Generator to write to
 * @param indenter Indenter used for the entries of the Object
 * @param level Nesting level of the closing bracket
 * @param entries Number of entries the Object has
 */
public static void writePrettyObjectEnd(JsonGenerator g, DefaultPrettyPrinter.Indenter indenter,
        int level, int entries) throws IOException
{
    WriterBasedJsonGenerator.writeIndentedEnd(g, indenter, level, entries, '}');
}'''

HOP3 = '''/**
 * Writes the closing marker of an Object or Array value in pretty-printed
 * output.
 *
 * @param g Generator to write to
 * @param indenter Indenter used for the entries of the value
 * @param level Nesting level of the closing marker
 * @param entries Number of entries the value has
 * @param marker Closing marker to write
 */
public static void writeIndentedEnd(JsonGenerator g, DefaultPrettyPrinter.Indenter indenter,
        int level, int entries, char marker) throws IOException
{
    JsonParser.prettyEndMarker(g, indenter, level, entries, marker);
}'''

HOP4 = '''/**
 * Writes the closing marker of an Object or Array value in pretty-printed
 * output.
 *
 * @param g Generator to write to
 * @param indenter Indenter used for the entries of the value
 * @param level Nesting level of the closing marker
 * @param entries Number of entries the value has
 * @param marker Closing marker to write
 */
public static void prettyEndMarker(JsonGenerator g, DefaultPrettyPrinter.Indenter indenter,
        int level, int entries, char marker) throws IOException
{
    UTF8StreamJsonParser.writeClosingMarker(g, indenter, level, entries, marker);
}'''

FACADE_HEAD = "    @Override\n    public void writeEndObject(JsonGenerator g, int nrOfEntries) throws IOException"
FACADE_JAVADOC = ("    /**\n"
                  "     * Method called after an Object value has been completely output,\n"
                  "     * to output the closing curly bracket with its white-space decoration.\n"
                  "     * The nesting level to use is recomputed by counting the Object and\n"
                  "     * Array scopes still open in the generator's output context, instead\n"
                  "     * of being read from a counter kept by this pretty printer.\n"
                  "     */\n")

DESIGN = {
 "instance": "JacksonCore-23", "project": "JacksonCore", "bug_id": 23, "seed": 3506,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "cell": "C10i", "batch": "batch8", "facade_variant": "V1",
 "state_passed": "the parameters g and nrOfEntries and the fields _objectIndenter and _nesting, passed to hop 1; write-back: "
                 "_nesting = hop 1's return value (the nesting level after the Object)",
 "host_mode": "1500", "host_lines": [2864, 2046, 1973, 1846, 3771],
 "reachability_probe": "writeEndObject first statement made to throw IllegalStateException(\"PROBE-REACHED\") in "
                       "/private/tmp/d4j-mi-JacksonCore-23-probe: TestPrettyPrinter::testCustomRootSeparatorWithPP fails with "
                       "PROBE-REACHED at DefaultPrettyPrinter.writeEndObject(DefaultPrettyPrinter.java:329) via "
                       "WriterBasedJsonGenerator.writeEndObject; the probe's full suite fails 11 tests (TestPrettyPrinter, "
                       "TestDefaultPrettyPrinter)",
 "facade": {"file": DPP, "class": "com.fasterxml.jackson.core.util.DefaultPrettyPrinter", "method": "writeEndObject", "near_line": 333},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/core/main/TestPrettyPrinter.java",
             "test_class": "com.fasterxml.jackson.core.main.TestPrettyPrinter", "test_method": "testCustomRootSeparatorWithPP"},
 "expected_signature": "expected:<{[ } { ]} [ ]> but was:<{[} {]} [ ]>",
 "gold": {"method": "writeClosingMarker", "text": GOLD_TEXT,
          "fault": {"old": "        if (entries > 0) {\n"
                           "            indenter.writeIndentation(g, level);\n"
                           "        } else {\n"
                           "            g.writeRaw(' ');\n"
                           "        }",
                    "new": "        if (entries > 0) {\n"
                           "            indenter.writeIndentation(g, level);\n"
                           "        }"}},
 "pre_edits": {"chain": [
   {"file": DPP, "old": FACADE_HEAD, "new": FACADE_JAVADOC + FACADE_HEAD},
   {"file": DPP, "old": "        g.writeRaw('}');", "new": "        g.writeRaw((char) 125);"},
 ]},
 "chain": {
   "facade_body": "_nesting = com.fasterxml.jackson.core.json.async.NonBlockingJsonParser.prettyObjectEnd(g, nrOfEntries, "
                  "_objectIndenter, _nesting);",
   "lie": LIE,
   "hops": [
     {"file": NBP, "class": "com.fasterxml.jackson.core.json.async.NonBlockingJsonParser", "method": "prettyObjectEnd",
      "imports": ["com.fasterxml.jackson.core.util.DefaultPrettyPrinter"], "text": HOP1},
     {"file": JG, "class": "com.fasterxml.jackson.core.JsonGenerator", "method": "writePrettyObjectEnd",
      "imports": ["com.fasterxml.jackson.core.json.WriterBasedJsonGenerator",
                  "com.fasterxml.jackson.core.util.DefaultPrettyPrinter"], "text": HOP2},
     {"file": WBG, "class": "com.fasterxml.jackson.core.json.WriterBasedJsonGenerator", "method": "writeIndentedEnd",
      "imports": ["com.fasterxml.jackson.core.util.DefaultPrettyPrinter"], "text": HOP3},
     {"file": JP, "class": "com.fasterxml.jackson.core.JsonParser", "method": "prettyEndMarker",
      "imports": ["com.fasterxml.jackson.core.json.UTF8StreamJsonParser",
                  "com.fasterxml.jackson.core.util.DefaultPrettyPrinter"], "text": HOP4},
     {"file": U8P, "class": "com.fasterxml.jackson.core.json.UTF8StreamJsonParser", "method": "writeClosingMarker",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.core.util.DefaultPrettyPrinter::writeEndArray",
              "com.fasterxml.jackson.core.json.WriterBasedJsonGenerator::writeEndArray",
              "com.fasterxml.jackson.core.json.UTF8JsonGenerator::writeEndArray"],
 "ownership_reason": "Only the gold decides what is written before the closing marker of a value: the indenter's indentation at the "
                     "marker's level when the value has entries, a single space otherwise, then the marker itself. Hop 1 only "
                     "computes the nesting level after the Object (and returns it for the facade's write-back of _nesting), hop 2 "
                     "only binds the Object's marker '}', and hops 3 and 4 pass the generator, indenter, level, entry count and marker "
                     "along unchanged; no hop writes anything after the gold returns. Once the gold has written '}' directly after "
                     "'{', the space of the layout can appear only if a caller writes it itself or hands the gold fabricated inputs. "
                     "The gold's javadoc promises the pretty-printed layout of DefaultPrettyPrinter, which closes a value without "
                     "entries as '{ }' / '[ ]'; the variant writes '{}'. The convention is pinned outside the gold: the intact "
                     "sibling DefaultPrettyPrinter.writeEndArray does the same step (`else { g.writeRaw(' '); }` for an array "
                     "without values) and is used in production by WriterBasedJsonGenerator.writeEndArray and "
                     "UTF8JsonGenerator.writeEndArray; testSystemLinefeed, testCustomSeparatorsWithPP and testRootSeparator pass "
                     "through the chain (an Object with entries closed on the indentation of its level, the level dropping back "
                     "after a nested Object, a NopIndenter Object closed with no white space).",
 "ownership_tests": ["com.fasterxml.jackson.core.util.TestDefaultPrettyPrinter::testSystemLinefeed",
                     "com.fasterxml.jackson.core.main.TestPrettyPrinter::testCustomSeparatorsWithPP",
                     "com.fasterxml.jackson.core.util.TestDefaultPrettyPrinter::testRootSeparator"],
 "compensating": {
   "chain": [
     {"file": NBP, "old": "final int level = indenter.isInline() ? nesting : (nesting - 1);",
      "new": "final int level = nesting - 1;",
      "why": "hop 1 always lowers the nesting level"},
     {"file": JG, "old": "WriterBasedJsonGenerator.writeIndentedEnd(g, indenter, level, entries, '}');",
      "new": "WriterBasedJsonGenerator.writeIndentedEnd(g, indenter, level, Math.max(entries, 1), '}');",
      "why": "hop 2 counts an Object as having at least one entry"},
     {"file": JP, "old": "UTF8StreamJsonParser.writeClosingMarker(g, indenter, level, entries, marker);",
      "new": "UTF8StreamJsonParser.writeClosingMarker(g, DefaultPrettyPrinter.FixedSpaceIndenter.instance, level, entries, marker);",
      "why": "hop 4 uses the single-space indenter"},
   ],
 },
 "host_notes": "host_mode 1500: hosts drawn by the recipe's seeded draw (mr_lib.py preview JacksonCore-23 "
               "com/fasterxml/jackson/core/util/DefaultPrettyPrinter.java 5, seed 3506; DefaultPrettyPrinter.java, the only allowed "
               "candidates' file, is excluded), used in draw order, none substituted: hop 1 json.async.NonBlockingJsonParser (2864 "
               "lines, anchor after releaseBuffered, seed 3606), hop 2 JsonGenerator (2046, after getCurrentValue, 3607), hop 3 "
               "json.WriterBasedJsonGenerator (1973, after writeNumber, 3608), hop 4 JsonParser (1846, after getObjectId, 3609), "
               "hop 5 json.UTF8StreamJsonParser (3771, gold, after getValueAsString, 3610). Smallest host: JsonParser, 1846 lines. "
               "All five are public top-level classes (JsonGenerator and JsonParser abstract) in which a public static method "
               "compiles. The facade calls hop 1 by its fully-qualified name; hops 1-4 import util.DefaultPrettyPrinter (for its "
               "public nested interface Indenter) and the next host where it is in another package; the gold's host already "
               "imports com.fasterxml.jackson.core.util.*.",
}
