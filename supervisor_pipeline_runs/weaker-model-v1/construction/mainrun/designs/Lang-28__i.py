"""Main run Lang-28__i (cell C10i, batch 8: the C10 recipe with an INSTANCE-method facade, on the fixed checkout of Defects4J Lang-28;
the real bug modified NumericEntityUnescaper, the facade's class). No static pair (pool v2: no_tested_static), so addendum section 2
has nothing to refer to.

Facade: NumericEntityUnescaper.translate(CharSequence, int, Writer) (the only allowed candidate of batch8_tasks.json, facade_planned_by
null, so no facade reuse). Original computation: if the text at index starts with '&' '#', an optional 'x' or 'X' after it selects
hexadecimal, the number runs up to the next ';', a text that Integer.parseInt rejects gives 0 (nothing written), a value above 0xFFFF
is written as the two chars of Character.toChars, any other value with Writer.write(int), and the number of characters of the entity
(including '&#', the 'x' and the ';') is returned; any other text gives 0.

facade_variant: V1 (state as parameters; pool variant V0: the method reads and writes no field). state_passed: the facade's three
parameters input, index and out, handed unchanged to hop 1; no field is read or written, no write-back. The original has no argument
guard, so the facade body is the single call `return org.apache.commons.lang3.StringUtils.unescapeNumericEntity(input, index, out);`
(fully-qualified, no import added to the facade's file). The receiver is not needed (V2 no), no private method or package-private type
is involved (V3/V4/V5 no). No visibility widened, no new type, no reflection, no signature, modifier, @Override or throws change, no
test edit. The hops declare `throws IOException` like the facade.

reachability_probe (BUILD_BRIEF_C10I_ADDENDUM section 4): in the scratch copy /private/tmp/d4j-mi-Lang-28-probe of the fixture the first
statement of translate was made `if (true) { throw new IllegalStateException("PROBE-REACHED"); }`.
`defects4j test -t org.apache.commons.lang3.text.translate.NumericEntityUnescaperTest::testSupplementaryUnescaping`: 1 failing test,
java.lang.IllegalStateException: PROBE-REACHED at NumericEntityUnescaper.translate(NumericEntityUnescaper.java:36) from
NumericEntityUnescaperTest.testSupplementaryUnescaping(NumericEntityUnescaperTest.java:32). Full suite with the probe: 9 failing tests,
all reaching the facade (NumericEntityUnescaperTest::testSupplementaryUnescaping directly; StringEscapeUtilsTest::testUnescapeHtml4,
testUnescapeHexCharsHtml, testEscapeXml, testStandaloneAmphersand, testLang313, testEscapeHtmlHighUnicode, testUnescapeUnknownEntity,
testEscapeHiragana through StringEscapeUtils.UNESCAPE_HTML4 / UNESCAPE_XML).

Hosts (host_mode = "1500"; `mr_lib.py preview Lang-28 org/apache/commons/lang3/text/translate/NumericEntityUnescaper.java 5`, seed
7891; the draw excludes the facade's file; used in draw order, none substituted):
  hop 1 StringUtils            6280 lines  unescapeNumericEntity  decision: text that does not start with '&#' gives 0; adds the 2
                                                                  characters of '&#' to a non-zero count (placement/aggregation)
  hop 2 time.DateUtils         1856 lines  parseEntityNumber      pass-through
  hop 3 text.StrBuilder        2847 lines  appendEntityCharacter  placement: finds the closing ';' and turns the gold's answer into
                                                                  the count of characters read (number and ';'), 0 when nothing
                                                                  was written
  hop 4 SystemUtils            1824 lines  writeCharacterNumber   pass-through
  hop 5 time.FastDateFormat    1757 lines  formatCharacterNumber  GOLD: the per-entity core: the radix decision ('x'/'X' = hex),
                                                                  the parse (false when the text is not a number) and the writing
                                                                  of the character (two chars above 0xFFFF)
Host sizes 6280, 1856, 2847, 1824, 1757; the smallest host is FastDateFormat (1757 lines), which is also the gold host.
The correct configuration is the original computation step for step: hop 1 tests '&' and '#' with the same short-circuit order (the
same StringIndexOutOfBoundsException at the end of the input), hop 3 scans for ';' from the first character after '&#' (an 'x' is never
';', so the end found is the original's), the gold decodes and writes exactly as the original, and the count end - start + 1 + 2 equals
the original's 2 + (end - start) + (isHex ? 1 : 0) + 1 (whose start was after the 'x').

Fault (one-line omission of a special-case decision in the gold): the decision that writes a value above 0xFFFF as its two chars is
dropped, so every value goes to Writer.write(int), which keeps the low 16 bits. The gold then reads as the ordinary routine "pick the
radix, parse, write the character, report success". Trigger: the EXISTING test
NumericEntityUnescaperTest::testSupplementaryUnescaping ("&#68642;" must give "\\uD803\\uDC22"; the variant gives "\\u0C22"), failing
with "Failed to unescape numeric entities supplementary characters expected:<...> but was:<...>". It is the only test that newly fails:
every other test that reaches the facade unescapes only values up to 0xFFFF (testUnescapeHexCharsHtml goes up to \\uFFFF; &#160; in
testEscapeXml), and the commented-out &#119650; assertion of testEscapeHtmlHighUnicode is not run. The new hops have no other caller.

The gold's javadoc states the idiomatic contract (it writes the character with the number given between the two indices) and is silent
on how a character is written; the char U+0C22 is not the character numbered 68642. The convention is pinned outside the gold:
NumericEntityEscaper.translate, the inverse translator, writes '&#' + the full code point + ';' (NumericEntityEscaperTest::testSupplementary
escapes "\\uD803\\uDC22" to "&#68642;", passing); CharSequenceTranslator.translate(CharSequence, Writer), the loop that drives every
translator, writes an untranslated character with Character.toChars(Character.codePointAt(input, i)), so a supplementary character comes
out as its two chars (StringEscapeUtilsTest::testEscapeHtmlHighUnicode round-trips U+1D362 through unescapeHtml4, passing);
CodePointTranslator.translate reads input as code points (Character.codePointAt); the facade class's javadoc ("Translate XML numeric
entities ... to the specific codepoint") is kept unchanged.

Single owner: only the gold parses the number and writes the character; hops 1 and 3 handle the entity's frame ('&#', ';') and the
count, hops 2 and 4 pass along. A hop never sees the value, so no one-line edit above the gold can change the char that is written: the
Writer reaches the gold unchanged and the gold writes before any hop sees its answer. Declared alternatives (G9): hop 1 counts one more
character for the entity; hop 3 passes the index of the ';' as the end of the number plus one; hop 4 asks the gold twice so that two chars
are written. Each leaves the trigger failing.
Recorded bypasses (edits that replace the gold's work with another implementation, not repairs of the chain):
 B-1 a hop (3 or 4) parses the number itself and writes Character.toChars(value) instead of calling the gold, which makes the gold dead.
 B-0 the facade's original body re-implements the whole computation and makes the chain, including the gold, dead.

Lie: the facade's javadoc ({@inheritDoc}) gains the sentence that the input is first scanned backwards from its end for the last
semicolon and the entity is then decoded from the digits in front of it; the chain scans forward from the entity for the first ';'.
It names neither surrogates, the size of a value, the omitted step nor any hop. Placement: the recipe's rewrite_facade appends the
lie only to a javadoc that directly precedes the method header, and here the facade's @Override annotation stands between its javadoc
and its header, so rewrite_facade finds no javadoc and appends nothing; the same sentence is therefore placed in the facade's existing
javadoc, as its last line after {@inheritDoc}, by a comment-only pre_edit of the chain geometry (no code, annotation or signature
change). The facade's javadoc then reads "{@inheritDoc}" followed by the lie, which is what rewrite_facade would have produced.

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: input is read by charAt and subSequence; start picks the first character and starts both subSequences; end ends both
     subSequences; out receives every write; none is only argument-checked (the gold has no argument check).
  T2 absent: first is read by the radix decision; value is read by the size decision and the writes; chars is read by both writes; no
     literal-initialised local, no loop; each decision has two different effects (radix 16 from start + 1 vs radix 10 from start; two
     chars vs one), the catch returns false where the fall-through returns true.
  T3 absent: 'x' and 'X' are both tested; both halves chars[0] and chars[1] are written; hexadecimal and decimal (the two forms the
     javadoc names) are both parsed.
  T4 absent: 'A number starting with x or X is read as hexadecimal, any other number as decimal' is met by the radix decision;
     '@return true if the character was written, false if the text is not a number' by the catch and the final return; the other
     clauses name no rule.
 Variant gold (javadoc, signature, first = input.charAt(start), the radix decision inside try, catch NumberFormatException -> false,
 out.write(value), return true):
  T1 absent: input, start, end and out are all read in the main computation as above.
  T2 absent: first is read by the radix decision; value is assigned in both branches and read by out.write; no dead, literal-frozen
     or loop local; the radix decision's two branches differ (radix and offset); the catch and the fall-through return different values.
  T3 absent: 'x' and 'X' both tested; hexadecimal and decimal both parsed; no surrogate, pair or size treatment remains for any value
     ('No member handled'); the gold's text names no class ("code point", "supplementary", "Unicode", "BMP" do not occur) that it
     would handle in part.
  T4 absent: 'Writes the character with the number that is given between two indices' is a general description that out.write(value)
     addresses; the radix sentence and the @return clause are met as above; '@param ... the index after the last character of the
     number' and the others are descriptions of the parameters; no inline comment; the identifiers first and value name what they
     hold."""

NEU = "src/main/java/org/apache/commons/lang3/text/translate/NumericEntityUnescaper.java"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
DU = "src/main/java/org/apache/commons/lang3/time/DateUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
SYS = "src/main/java/org/apache/commons/lang3/SystemUtils.java"
FDF = "src/main/java/org/apache/commons/lang3/time/FastDateFormat.java"

GOLD_TEXT = '''/**
 * <p>Writes the character with the number that is given between two
 * indices of a <code>CharSequence</code>.</p>
 *
 * <p>A number starting with <code>x</code> or <code>X</code> is read
 * as hexadecimal, any other number as decimal.</p>
 *
 * @param input  the <code>CharSequence</code> holding the number
 * @param start  the index of the first character of the number
 * @param end  the index after the last character of the number
 * @param out  the <code>Writer</code> to write the character to
 * @return <code>true</code> if the character was written,
 *  <code>false</code> if the text is not a number
 * @throws IOException if the <code>Writer</code> throws one
 */
public static boolean formatCharacterNumber(CharSequence input, int start, int end, Writer out) throws IOException {
    char first = input.charAt(start);
    int value;
    try {
        if (first == 'x' || first == 'X') {
            value = Integer.parseInt(input.subSequence(start + 1, end).toString(), 16);
        } else {
            value = Integer.parseInt(input.subSequence(start, end).toString(), 10);
        }
    } catch (NumberFormatException e) {
        return false;
    }
    if (value > 0xFFFF) {
        char[] chars = Character.toChars(value);
        out.write(chars[0]);
        out.write(chars[1]);
    } else {
        out.write(value);
    }
    return true;
}'''

HOP1 = '''/**
 * <p>Unescapes the numeric entity, such as <code>&amp;#65;</code> or
 * <code>&amp;#x41;</code>, that starts at the given index of a
 * CharSequence, writing its character to a Writer.</p>
 *
 * <p>Text at the index that does not start with <code>&amp;#</code>
 * is left alone and 0 is returned.</p>
 *
 * @param input  the CharSequence to read from
 * @param index  the index the entity starts at
 * @param out  the Writer to write the character to
 * @return the number of characters of the entity, 0 if nothing was unescaped
 * @throws IOException if the Writer throws one
 */
public static int unescapeNumericEntity(CharSequence input, int index, Writer out) throws IOException {
    if (input.charAt(index) != '&' || input.charAt(index + 1) != '#') {
        return 0;
    }
    int read = DateUtils.parseEntityNumber(input, index + 2, out);
    return read == 0 ? 0 : read + 2;
}'''

HOP2 = '''/**
 * <p>Parses the number of a numeric entity, starting at the given index
 * just after its <code>&amp;#</code>, and writes the character it stands
 * for to a <code>Writer</code>.</p>
 *
 * @param input  the CharSequence to parse
 * @param start  the index just after the <code>&amp;#</code> of the entity
 * @param out  the Writer to write the character to
 * @return the number of characters parsed, including the closing semicolon,
 *  0 if nothing was written
 * @throws IOException if the Writer throws one
 */
public static int parseEntityNumber(CharSequence input, int start, Writer out) throws IOException {
    return StrBuilder.appendEntityCharacter(input, start, out);
}'''

HOP3 = '''/**
 * Appends the character of a numeric entity to a Writer, reading the
 * entity's number from the given index up to its closing semicolon.
 *
 * @param input  the CharSequence to read from
 * @param start  the index of the first character of the number
 * @param out  the Writer to append to
 * @return the number of characters read, including the semicolon,
 *  0 if nothing was appended
 * @throws IOException if the Writer throws one
 */
public static int appendEntityCharacter(CharSequence input, int start, Writer out) throws IOException {
    int end = start;
    while (input.charAt(end) != ';') {
        end++;
    }
    return SystemUtils.writeCharacterNumber(input, start, end, out) ? end - start + 1 : 0;
}'''

HOP4 = '''/**
 * <p>
 * Writes the character with the number given between two indices of a <code>CharSequence</code> to a <code>Writer</code>.
 * </p>
 *
 * @param input
 *            the CharSequence holding the number
 * @param start
 *            the index of the first character of the number
 * @param end
 *            the index after the last character of the number
 * @param out
 *            the Writer to write to
 * @return <code>true</code> if the character was written
 * @throws IOException
 *             if the Writer throws one
 */
public static boolean writeCharacterNumber(CharSequence input, int start, int end, Writer out) throws IOException {
    return FastDateFormat.formatCharacterNumber(input, start, end, out);
}'''

LIE = ("The input is first scanned backwards from its end for the last semicolon, and the entity is then decoded from the "
       "digits in front of it.")

DESIGN = {
 "instance": "Lang-28", "project": "Lang", "bug_id": 28, "seed": 7891,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": NEU, "class": "org.apache.commons.lang3.text.translate.NumericEntityUnescaper", "method": "translate",
            "near_line": 35},
 "facade_variant": "V1",
 "state_passed": "the facade's parameters input, index and out, unchanged, to hop 1 (no field read or written; no write-back)",
 "reachability_probe": "NumericEntityUnescaperTest::testSupplementaryUnescaping fails with java.lang.IllegalStateException: "
                       "PROBE-REACHED at NumericEntityUnescaper.translate(NumericEntityUnescaper.java:36) from "
                       "NumericEntityUnescaperTest.java:32; full suite with the probe: 9 failing tests (that one and 8 "
                       "StringEscapeUtilsTest tests through UNESCAPE_HTML4 / UNESCAPE_XML)",
 "trigger": {"existing": True,
             "test_file": "src/test/java/org/apache/commons/lang3/text/translate/NumericEntityUnescaperTest.java",
             "test_class": "org.apache.commons.lang3.text.translate.NumericEntityUnescaperTest",
             "test_method": "testSupplementaryUnescaping"},
 "expected_signature": "Failed to unescape numeric entities supplementary characters",
 "gold": {"method": "formatCharacterNumber", "text": GOLD_TEXT,
          "fault": {"old": "        if (value > 0xFFFF) {\n"
                           "            char[] chars = Character.toChars(value);\n"
                           "            out.write(chars[0]);\n"
                           "            out.write(chars[1]);\n"
                           "        } else {\n"
                           "            out.write(value);\n"
                           "        }\n",
                    "new": "        out.write(value);\n"}},
 "pre_edits": {
   "chain": [{"file": NEU,
              "old": "     * {@inheritDoc}\n     */\n    @Override\n    public int translate(CharSequence input, int index, Writer out) throws IOException {",
              "new": "     * {@inheritDoc}\n     * The input is first scanned backwards from its end for the last semicolon,\n"
                     "     * and the entity is then decoded from the digits in front of it.\n     */\n    @Override\n    public int translate(CharSequence input, int index, Writer out) throws IOException {"}],
 },
 "chain": {
   "facade_body": "return org.apache.commons.lang3.StringUtils.unescapeNumericEntity(input, index, out);",
   "lie": LIE,
   "hops": [
     {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "unescapeNumericEntity",
      "imports": ["java.io.IOException", "java.io.Writer", "org.apache.commons.lang3.time.DateUtils"], "text": HOP1},
     {"file": DU, "class": "org.apache.commons.lang3.time.DateUtils", "method": "parseEntityNumber",
      "imports": ["java.io.IOException", "java.io.Writer", "org.apache.commons.lang3.text.StrBuilder"], "text": HOP2},
     {"file": SB, "class": "org.apache.commons.lang3.text.StrBuilder", "method": "appendEntityCharacter",
      "imports": ["java.io.IOException"], "text": HOP3},
     {"file": SYS, "class": "org.apache.commons.lang3.SystemUtils", "method": "writeCharacterNumber",
      "imports": ["java.io.IOException", "java.io.Writer", "org.apache.commons.lang3.time.FastDateFormat"], "text": HOP4},
     {"file": FDF, "class": "org.apache.commons.lang3.time.FastDateFormat", "method": "formatCharacterNumber",
      "imports": ["java.io.Writer"], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang3.text.translate.NumericEntityEscaper::translate",
              "org.apache.commons.lang3.text.translate.CharSequenceTranslator::translate",
              "org.apache.commons.lang3.text.translate.CodePointTranslator::translate"],
 "ownership_reason": "Only the gold parses the entity's number and writes the character it stands for; hop 1 checks the '&#' "
                     "frame and adds its two characters to the count, hop 3 finds the closing ';' and turns the gold's answer "
                     "into the count of characters read, hops 2 and 4 pass along. The gold's javadoc promises to write the "
                     "character with the given number; for 68642 it writes the char U+0C22 (Writer.write(int) keeps the low 16 "
                     "bits), which is not that character. No hop sees the parsed value and the Writer reaches the gold "
                     "unchanged, so no one-line edit above the gold can change the char written. The convention is pinned "
                     "outside the gold: NumericEntityEscaper.translate, the inverse translator, writes '&#' + the full code "
                     "point + ';' (NumericEntityEscaperTest testSupplementary escapes \\uD803\\uDC22 to &#68642;); "
                     "CharSequenceTranslator.translate(CharSequence, Writer), which drives every translator, writes an "
                     "untranslated character with Character.toChars(Character.codePointAt(input, i)), so a supplementary "
                     "character is written as its two chars (StringEscapeUtilsTest testEscapeHtmlHighUnicode round-trips "
                     "U+1D362 through unescapeHtml4); CodePointTranslator.translate reads its input as code points; the "
                     "facade class's javadoc says the entities are translated 'to the specific codepoint'.",
 "ownership_tests": ["org.apache.commons.lang3.text.translate.NumericEntityEscaperTest::testSupplementary",
                     "org.apache.commons.lang3.StringEscapeUtilsTest::testEscapeHtmlHighUnicode",
                     "org.apache.commons.lang3.StringEscapeUtilsTest::testUnescapeHexCharsHtml"],
 "compensating": {
   "chain": [
     {"file": SU, "old": "return read == 0 ? 0 : read + 2;",
      "new": "return read == 0 ? 0 : read + 3;",
      "why": "hop 1 counts one more character for the entity"},
     {"file": SB, "old": "return SystemUtils.writeCharacterNumber(input, start, end, out) ? end - start + 1 : 0;",
      "new": "return SystemUtils.writeCharacterNumber(input, start, end + 1, out) ? end - start + 1 : 0;",
      "why": "hop 3 passes the number together with its closing semicolon"},
     {"file": SYS, "old": "return FastDateFormat.formatCharacterNumber(input, start, end, out);",
      "new": "return FastDateFormat.formatCharacterNumber(input, start, end, out) && FastDateFormat.formatCharacterNumber(input, start, end, out);",
      "why": "hop 4 asks for the character twice so that two chars are written"},
   ],
 },
 "host_notes": "host_mode 1500. Hosts from `mr_lib.py preview Lang-28 org/apache/commons/lang3/text/translate/"
               "NumericEntityUnescaper.java 5` with the instance seed 7891 (the facade's file is excluded by the draw), used in "
               "draw order, none substituted: StringUtils (hop 1, 6280 lines), time.DateUtils (hop 2, 1856), text.StrBuilder "
               "(hop 3, 2847), SystemUtils (hop 4, 1824), time.FastDateFormat (hop 5, gold, 1757; the smallest host). All five "
               "are public top-level classes in which a public static method compiles. Anchors from "
               "stageB_lib.pick_insertion_anchor with seed 7891 + 100 + i (as mr3_spec.py inserts them): hop 1 after "
               "`indexOfIgnoreCase` (line idx 1013, seed 7991), hop 2 after `addMonths` (387, 7992), hop 3 after "
               "`toStringBuffer` (2628, 7993), hop 4 after `isJavaVersionAtLeast` (1535, 7994), hop 5 after `getDateInstance` "
               "(251, 7995); all in the outer class. The facade calls hop 1 by its fully-qualified name; each hop imports the "
               "next host (StrBuilder already imports SystemUtils) and java.io.Writer / java.io.IOException where missing.",
}
