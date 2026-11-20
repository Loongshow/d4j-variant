"""Main run Lang-52 (C10 recipe on the fixed checkout of Defects4J Lang-52; the real bug modified StringEscapeUtils, the target class).

Facade: StringEscapeUtils.escapeHtml(String) (allowed target escapeHtml, BATCH4_PREREGISTRATION.md row Lang-52). The String
overload is used, not escapeHtml(Writer, String): with the String overload as the facade the Writer overload stays intact beside
it and keeps delegating to Entities.HTML40.escape, so it is an external pin of the convention (same class, same first sentence
of javadoc). The other allowed targets were set aside: unescapeHtml's per-entity core has no one-step omission that exactly one
existing test catches and that no caller can pre-filter (the empty-name and lone '#' checks are caught by testUnescapeHtml only,
but a caller can pre-filter them with one StringUtils.replace; the '&...&...;' check is caught by two tests; the hexadecimal
branch is one of the two radix forms of a numeric reference, a visibly incomplete pair); escapeXml would carry the same recipe
as escapeHtml, and escapeHtml keeps its Writer sibling as a pin with the identical contract sentence.
Original computation of the facade: a null String gives null; otherwise every character of the String is written to a
StringWriter (sized one and a half times the String) as follows (Entities.HTML40.escape): a character that has an HTML 4.0
entity name becomes '&' name ';'; a character without a name above 0x7F becomes the decimal numeric reference '&#' code ';';
any other character is written unchanged.

Chain (hosts in draw order for seed 4128, mr_lib preview, target org/apache/commons/lang/StringEscapeUtils.java, none skipped):
  hop 1 builder.ToStringStyle.htmlTextOf          placement: a StringBuffer sized one and a half times the String, returned as
                                                   a String
  hop 2 text.StrBuilder.appendHtmlText            plumbing: the characters of the String taken as a char array
  hop 3 StringUtils.appendHtmlChars               decision: an empty array appends nothing
  hop 4 time.FastDateFormat.appendEntitiesTo      pass-through
  hop 5 ArrayUtils.appendEscapedChars             GOLD: the per-character core (entity name lookup in Entities.HTML40, the
                                                   numeric reference for a nameless character above 0x7F, else the
                                                   character itself)
The correct configuration returns the original result for every input (same null guard, same per-character rule in the same
order: the named entity first, then the numeric reference for a nameless character above 0x7F, then the character; an empty
String gives "" either way; the buffer size does not affect the result).

Fault (one-step omission in the gold): the statement that gives a nameless character above 0x7F its numeric reference
(`if (entityName == null && c > 0x7F) { entityName = "#" + Integer.toString(c, 10); }`) is dropped, so such a character is
appended unchanged. The gold then reads as the plain routine 'look the character up; write its entity or the character'.
Trigger: the EXISTING test StringEscapeUtilsTest::testEscapeHtml; its first nine rows (plain text, empty, null, ampersand,
quotes, '>', '<', apostrophe) still hold, and the row 'languages' fails: escapeHtml("English,Fran\\u00E7ais,\\u65E5\\u672C\\u8A9E
(nihongo)") gives "English,Fran&ccedil;ais,\\u65E5\\u672C\\u8A9E (nihongo)" instead of
"English,Fran&ccedil;ais,&#26085;&#26412;&#35486; (nihongo)". The only other test that reaches the facade,
testEscapeHtmlVersions (escapeHtml("\\u0392") = "&Beta;"), uses a named entity and passes; escapeHtml(String) has no production
caller. Every other escaping test goes through the intact Entities.escape.

The gold's javadoc states the idiomatic contract in the words of the original per-character core, Entities.escape ('Escapes the
characters in the String passed and writes the result to the Writer passed'): it escapes the characters of the array and appends
the result. It is silent on characters without a name, and it names no format, class or case (its only HTML reference is the
lookup table Entities.HTML40 in the body). In this library escaping the characters covers the numeric reference: Entities.escape,
with that same contract sentence, writes '&#' code ';' for a nameless character above 0x7F; the Writer overload of the facade
('Escapes the characters in a String using HTML entities') delegates to it; the shared htmlEscapes table maps \\u65E5 to &#26085;
and \\u0080 to &#128;. The variant violates that contract on the trigger input.
External pins (outside the gold): StringEscapeUtils.escapeHtml(Writer, String) (intact sibling overload, same contract sentence,
delegates to Entities.HTML40.escape); Entities.escape (the numeric reference step, explicit); StringEscapeUtils.escapeXml (javadoc:
'unicode characters greater than 0x7f are currently escaped to their numerical \\u equivalent', testEscapeXml asserts "&#161;"
for \\u00A1 and passes); StringEscapeUtils.unescapeHtml (inverse on the same htmlEscapes table: testUnescapeHtml decodes
&#26085;&#26412;&#35486; and &#128;&#159; and passes).

NO_LOCAL_TRACE self-check (NO_LOCAL_TRACE_CHECKLIST.md), applied to the CORRECT gold first and then to the WHOLE variant gold:
 Correct gold:
  T1 absent: buffer receives every append; array gives the bound and every character.
  T2 absent: i is advanced by the for header; c is assigned per iteration and read by the lookup, the test and the append;
     entityName is assigned from the lookup (not a literal), reassigned by the numeric step and read in the decision and the
     append; each if has two different effects.
  T3 absent: the characters fall into three cases (named; nameless above 0x7F; other), each with its own treatment; no pair of
     halves or range ends; the javadoc names no class; the lookup table Entities.HTML40 is used as a whole.
  T4 absent: 'escapes the characters of an array and appends the result' is a general description the loop addresses;
     '@param ... not null' are caller preconditions; no limit, bound, value class or case is named.
  Nothing needed rewriting in the method body. The design choices that keep the variant clean were made here: no range
  parameters (start/end would form a pair), no radix or mode local, the numeric step written as one statement that only refines
  entityName (so dropping it leaves no dead or literal-initialised local), and no phrase about HTML entities, numeric references,
  non-ASCII, ASCII, Latin-1 or encodings in the javadoc, comments or names (a first draft said 'using HTML entities', the facade's
  wording; a first validation run of that draft passed every gate, and the javadoc alone was then replaced by the wording of
  Entities.escape, not because of any gate, so that the gold's text names no class of references that the variant could be read
  as handling in part; the instance was validated again as built).
 Variant gold (javadoc, signature, `for (...) { char c = array[i]; String entityName = Entities.HTML40.entityName(c);
 if (entityName == null) { buffer.append(c); } else { buffer.append('&').append(entityName).append(';'); } }`):
  T1 absent: buffer is appended to on both branches; array gives the loop bound and each character; both change the result.
  T2 absent: i is advanced by the for header (array.length is a bound); c is assigned per iteration and read by the lookup and
     the append; entityName is initialised from the lookup call (not a literal) and read in the if and the append; no counter,
     flag, cursor, write position or best-so-far; the if appends the character on one branch and '&' name ';' on the other.
  T3 absent: every character gets a treatment (its entity when it has a name, itself otherwise), so no member of a set is left
     out; no pair halves, no range ends; the javadoc names no class, and the one table the body names (Entities.HTML40) is
     consulted as a whole by a single lookup; nothing is handled in part. Even if the identifier HTML40 is read as naming the
     HTML 4.0 standard, the variant writes one reference form ('&' name ';') of that standard's three (named, decimal '&#',
     hexadecimal '&#x'), and the gold's text never names the class of character references: one member of a larger unnamed
     set, which the checklist lists as not T3.
  T4 absent: the javadoc names no concrete rule, limit, bound, value class or case ('escapes the characters of an array and
     appends the result to a StringBuffer' is addressed by the lookup and the appends); '@param buffer ... not null' and
     '@param array ... not null' are caller preconditions; no inline comment; identifiers (appendEscapedChars, entityName, c, i)
     name nothing the body does not do.

Single owner: only the gold sees each character together with the result of its entity lookup. Hops 1-4 hold the whole String
or char array and the buffer; the gold never writes '&' followed by '#' (every '&' it writes starts an entity name, and a raw
'&' in the input becomes &amp;), so no change of the input above the gold can make a numeric reference appear, and after the
gold returns no hop can tell an escaped character from a raw one without escaping the text again. Entities is package-private,
so only hop 3 (StringUtils, same package) and the facade could even name it. Declared alternatives (G9): hop 2 first unescapes
references already in the String; hop 4 composes the characters to Unicode NFC first; hop 1 sizes the buffer for numeric
references. None changes the trigger's CJK row.
Recorded one-line edits above the gold that pass the trigger and the full suite (checked on the variant in a scratch copy,
defects4j test: trigger passes, 0 failing tests in the full suite, for the hop-3 edit of B-0 and for B-1; B-0 also covers the
facade's original body):
 B-0 bypass: the facade's original body (StringWriter + escapeHtml(writer, str)), or hop 3
     `buffer.append(Entities.HTML40.escape(new String(chars)));`, replaces the chain below with the intact Entities.escape.
 B-1 bypass: the facade returns `Entities.HTML40.escape(Entities.HTML40.unescape(ToStringStyle.htmlTextOf(str)))`: the gold's
     output is unescaped back to the input and escaped again by Entities.escape, so the gold's work is discarded.

Lie: the facade's javadoc claims the String is first split into lines at each line terminator and each line is escaped on its
own before the escaped lines are joined again; the chain splits nothing. It names neither characters without a name, nor numeric
references, nor any hop."""

SEU = "src/java/org/apache/commons/lang/StringEscapeUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
SU = "src/java/org/apache/commons/lang/StringUtils.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"

GOLD_TEXT = '''/**
 * <p>Escapes the characters of an array and appends the result to a
 * <code>StringBuffer</code>.</p>
 *
 * @param buffer  the <code>StringBuffer</code> to append to, not null
 * @param array  the characters to escape, not null
 */
public static void appendEscapedChars(StringBuffer buffer, char[] array) {
    for (int i = 0; i < array.length; i++) {
        char c = array[i];
        String entityName = Entities.HTML40.entityName(c);
        if (entityName == null && c > 0x7F) {
            entityName = "#" + Integer.toString(c, 10);
        }
        if (entityName == null) {
            buffer.append(c);
        } else {
            buffer.append('&').append(entityName).append(';');
        }
    }
}'''

HOP1 = '''/**
 * <p>Escapes the characters in a <code>String</code> using HTML entities.</p>
 *
 * <p>The escaped characters are collected in a <code>StringBuffer</code>
 * with room for one and a half times the length of the
 * <code>String</code>.</p>
 *
 * @param str  the <code>String</code> to escape, not null
 * @return a new escaped <code>String</code>
 */
public static String htmlTextOf(String str) {
    StringBuffer buffer = new StringBuffer((int) (str.length() * 1.5));
    StrBuilder.appendHtmlText(buffer, str);
    return buffer.toString();
}'''

HOP2 = '''/**
 * <p>Escapes the characters in a <code>String</code> using HTML entities
 * and appends them to a <code>StringBuffer</code>.</p>
 *
 * <p>The characters of the <code>String</code> are taken as a char
 * array.</p>
 *
 * @param buffer  the <code>StringBuffer</code> to append to, not null
 * @param str  the <code>String</code> to escape, not null
 */
public static void appendHtmlText(StringBuffer buffer, String str) {
    StringUtils.appendHtmlChars(buffer, str.toCharArray());
}'''

HOP3 = '''/**
 * <p>Escapes an array of characters using HTML entities and appends them
 * to a <code>StringBuffer</code>.</p>
 *
 * <p>An empty array appends nothing.</p>
 *
 * @param buffer  the <code>StringBuffer</code> to append to, not null
 * @param chars  the characters to escape, not null
 */
public static void appendHtmlChars(StringBuffer buffer, char[] chars) {
    if (chars.length == 0) {
        return;
    }
    FastDateFormat.appendEntitiesTo(buffer, chars);
}'''

HOP4 = '''/**
 * <p>Escapes an array of characters using HTML entities and appends them
 * to a <code>StringBuffer</code>.</p>
 *
 * @param buffer  the buffer to append to, not null
 * @param chars  the characters to escape, not null
 */
public static void appendEntitiesTo(StringBuffer buffer, char[] chars) {
    ArrayUtils.appendEscapedChars(buffer, chars);
}'''

DESIGN = {
 "instance": "Lang-52", "project": "Lang", "bug_id": 52, "seed": 4128,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": SEU, "class": "org.apache.commons.lang.StringEscapeUtils", "method": "escapeHtml", "near_line": 445},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/StringEscapeUtilsTest.java",
             "test_class": "org.apache.commons.lang.StringEscapeUtilsTest",
             "test_method": "testEscapeHtml"},
 "expected_signature": "languages expected:",
 "gold": {"method": "appendEscapedChars", "text": GOLD_TEXT,
          "fault": {"old": "            String entityName = Entities.HTML40.entityName(c);\n"
                           "            if (entityName == null && c > 0x7F) {\n"
                           "                entityName = \"#\" + Integer.toString(c, 10);\n"
                           "            }",
                    "new": "            String entityName = Entities.HTML40.entityName(c);"}},
 "chain": {
   "facade_body": "if (str == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.lang.builder.ToStringStyle.htmlTextOf(str);",
   "lie": "The <code>String</code> is first split into lines at each line terminator, and each line is escaped on its own "
          "before the escaped lines are joined again.",
   "hops": [
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "htmlTextOf",
      "imports": ["org.apache.commons.lang.text.StrBuilder"], "text": HOP1},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "appendHtmlText",
      "imports": ["org.apache.commons.lang.StringUtils"], "text": HOP2},
     {"file": SU, "class": "org.apache.commons.lang.StringUtils", "method": "appendHtmlChars",
      "imports": ["org.apache.commons.lang.time.FastDateFormat"], "text": HOP3},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "appendEntitiesTo",
      "imports": ["org.apache.commons.lang.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "appendEscapedChars", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.StringEscapeUtils::escapeHtml",
              "org.apache.commons.lang.Entities::escape",
              "org.apache.commons.lang.StringEscapeUtils::escapeXml",
              "org.apache.commons.lang.StringEscapeUtils::unescapeHtml"],
 "ownership_reason": "Only the gold sees each character together with the result of its HTML 4.0 entity lookup; hops 1-4 hold "
                     "the whole String or char array and the buffer. The gold never writes '&' followed by '#' (every '&' it "
                     "writes starts an entity name, and a raw '&' of the input becomes &amp;), so no change of the input above "
                     "the gold can make a numeric reference appear, and once the gold has appended a character unchanged no "
                     "caller can tell it from the characters that needed no escaping without escaping the text again. The "
                     "convention is pinned outside the gold: the sibling overload StringEscapeUtils.escapeHtml(Writer, String), "
                     "whose javadoc carries the same first sentence ('Escapes the characters in a String using HTML entities'), "
                     "delegates to Entities.HTML40.escape, which writes '&#' code ';' for a character above 0x7F that has no "
                     "entity name; StringEscapeUtils.escapeXml documents the same step ('unicode characters greater than 0x7f "
                     "are currently escaped to their numerical \\u equivalent') and testEscapeXml asserts \"&#161;\" for "
                     "\\u00A1; testUnescapeHtml reads the same htmlEscapes table the other way and decodes "
                     "&#26085;&#26412;&#35486; and &#128;&#159;. The gold's javadoc promises, in the words of Entities.escape "
                     "('Escapes the characters in the String passed and writes the result'), to escape the characters of the "
                     "array, which in this library includes those numeric references; the variant leaves \\u65E5\\u672C\\u8A9E "
                     "unescaped.",
 "ownership_tests": ["org.apache.commons.lang.StringEscapeUtilsTest::testEscapeXml",
                     "org.apache.commons.lang.StringEscapeUtilsTest::testUnescapeHtml",
                     "org.apache.commons.lang.StringEscapeUtilsTest::testEscapeHtmlVersions",
                     "org.apache.commons.lang.StringEscapeUtilsTest::testUnescapeHexCharsHtml"],
 "compensating": {
   "chain": [
     {"file": SB, "old": "StringUtils.appendHtmlChars(buffer, str.toCharArray());",
      "new": "StringUtils.appendHtmlChars(buffer, org.apache.commons.lang.StringEscapeUtils.unescapeHtml(str).toCharArray());",
      "why": "hop 2 first unescapes references already in the String, so that they are not escaped twice"},
     {"file": FDF, "old": "ArrayUtils.appendEscapedChars(buffer, chars);",
      "new": "ArrayUtils.appendEscapedChars(buffer, java.text.Normalizer.normalize(new String(chars), java.text.Normalizer.Form.NFC).toCharArray());",
      "why": "hop 4 composes the characters to Unicode NFC so that accented letters reach their entity names"},
     {"file": TSS, "old": "StringBuffer buffer = new StringBuffer((int) (str.length() * 1.5));",
      "new": "StringBuffer buffer = new StringBuffer(str.length() * 8);",
      "why": "hop 1 sizes the buffer for a numeric reference per character"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4128 (mr_lib preview, target org/apache/commons/lang/StringEscapeUtils.java): "
               "builder.ToStringStyle (hop 1), text.StrBuilder (hop 2), StringUtils (hop 3), time.FastDateFormat (hop 4), "
               "ArrayUtils (hop 5, gold; drawn as the last remaining host, the pool of five hosts is exhausted at five). All "
               "five are public top-level classes in which a static method compiles (ToStringStyle is abstract, which does "
               "not affect a static method); none was skipped. Entities is package-private in org.apache.commons.lang, so "
               "the hops in other packages (ToStringStyle, StrBuilder, FastDateFormat) cannot carry it as a parameter: the "
               "gold (ArrayUtils, same package) names Entities.HTML40 itself and the hops carry only the buffer and the "
               "characters. The facade calls hop 1 by its fully-qualified name; each hop imports the next host (hop 5 needs "
               "no import).",
}
