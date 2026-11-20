"""Main run Lang-46 (C10 recipe on the fixed checkout of Defects4J Lang-46; the real bug modified StringEscapeUtils, the target
class).

Facade: StringEscapeUtils.escapeCsv(String) (allowed target, pool candidate escapeCsv). unescapeCsv was set aside: every step of
its computation (the length and enclosure checks, the content test, the collapse of doubled quotes) can be reproduced or undone
by a one-line StringUtils call at any hop that holds the field (containsAny / replace), so no omission in an unescape gold has a
unique owner. Of the two escapeCsv overloads the String one is the facade: escapeCsv(String) delegates to the Writer overload
(the 16-line pool entry) and the two tests run the same inputs, so a chain behind the Writer overload would fail both tests (G5).
In escapeCsv(String) the original body delegates to the Writer overload escapeCsv(Writer, String); the facade now
keeps a null guard (the original returned null for null through containsNone) and delegates to a five-hop chain drawn with the
instance seed 4967 (mr_lib preview, draw order, no substitution):
  hop 1 time.DateUtils.lineFieldOf            placement: the comma as the delimiter of the line
  hop 2 builder.ToStringStyle.fieldFor        aggregation: the characters searched for (the delimiter and the two line breaks)
  hop 3 text.StrBuilder.fieldText             decision: an empty value is its own field
  hop 4 time.FastDateFormat.textAsField       pass-through
  hop 5 ArrayUtils.toField                    GOLD: the per-character pass (a double quote is written twice and makes the
                                              field enclosed; a search character makes the field enclosed; the field is the
                                              enclosed buffer or the value itself)
The correct configuration computes exactly the original result for every input (null -> null; a value with none of
',', '"', CR, LF -> the value; otherwise '"' + value with each '"' doubled + '"'). The Writer overload escapeCsv(Writer, String),
unescapeCsv and the CSV constants are untouched.

Fault (one-line omission in the gold, in the iteration's enclosure decision): the statement `enclose = true;` in the double-quote
branch is dropped, so a double quote is still written twice into the buffer but no longer makes the field enclosed; a value whose
only special character is a double quote is returned as it is. Trigger: the EXISTING test StringEscapeUtilsTest::testEscapeCsvString;
its first four assertions pass (plain value, comma, LF, CR) and the assertion escapeCsv("foo\"bar") expects "\"foo\"\"bar\"" and
gets "foo\"bar". It is the only caller of escapeCsv(String) in the code base (no production caller); testEscapeCsvWriter calls the
intact Writer overload with the same inputs and keeps passing.

The gold's javadoc states the idiomatic contract (a value as a field of a delimited line of text: the value itself, or the value
enclosed in double quotes with each double quote written twice) and is silent on which values are enclosed. The rule that a
double quote forces enclosure is pinned outside the gold: the facade's own javadoc ('If the value contains a comma, newline or
double quote, then the String value is returned enclosed in double quotes'); the sibling overload escapeCsv(Writer, String) decides
enclosure with containsNone over CSV_SEARCH_CHARS = {',', '"', CR, LF} and testEscapeCsvWriter expects "\"foo\"\"bar\"" for
"foo\"bar"; unescapeCsv treats a quoted field whose content holds a double quote as escaped (testUnescapeCsvString:
"\"foo\"\"bar\"" -> "foo\"bar"); StrTokenizer (the CSV reader of the code base) treats a double quote outside a quoted section as
the start of one, so an unenclosed field holding a double quote does not read back (StrTokenizerTest::testBasicQuoted5
"'b'x'c'" -> "bxc", testBasicQuoted3 "'b''c'" -> "b'c").

Single owner: only the gold visits the characters of the value. The double-quote branch comes before the search-character test
(if / else if), so no search set supplied from above can make a double quote enclose the field, and pre-doubling the quotes above
the gold only doubles them again. The gold discards its buffer when it does not enclose, so no caller can recover the field from
the returned value without re-implementing it. Declared alternatives (G9): hop 2 adds the double quote to the search characters
(no effect: the quote never reaches the search test), hop 4 passes the value with its double quotes already doubled (returns
"foo\"\"bar" unenclosed), hop 1 passes the double quote as the delimiter (commas no longer enclose); none passes the trigger.
Recorded bypasses (not declared; they absorb the trigger; B-1, B-2 and B-3 were applied to the variant in scratch copies: trigger passes, full suite 0 failing tests):
 B-0 the facade restores the original try/StringWriter/escapeCsv(Writer, String) body, discarding all five hops (multi-line).
 B-1 a hop above the gold returns its own enclosed form for a value holding a double quote, e.g. hop 3
     `if (value.indexOf('"') >= 0) { return '"' + org.apache.commons.lang.StringUtils.replace(value, "\"", "\"\"") + '"'; }`:
     it replaces the gold's result for that case with a second implementation.
 B-2 hop 4 passes the value itself as the search characters when it holds a double quote
     (`ArrayUtils.toField(value, value.indexOf('"') >= 0 ? value : searchChars)`): every other character of the value then
     forces enclosure; it contradicts the documented meaning of searchChars (the delimiter and the line breaks) and still leaves
     a value made only of double quotes unenclosed (test-fitted, not a repair).
 B-3 hop 4 re-wraps the gold's output: for a value holding a double quote it calls the gold on the value with the first search character appended
     (which encloses it), chops the closing quote and that character and appends a quote again
     (`value.indexOf('"') < 0 ? ArrayUtils.toField(value, searchChars) : StringUtils.chop(StringUtils.chop(ArrayUtils.toField(value + searchChars.charAt(0), searchChars))) + '"'`):
     it feeds the gold a different value and edits its result, so it is a test-fitted rewrite of the gold's output, not a repair
     that keeps each method used as documented.

Lie: the facade's javadoc claims the characters are visited from the last to the first, each inserted at the front of the buffer
that holds the field; the code writes the characters forwards with appends. It names neither double quotes, nor enclosure, nor
any hop.

No-local-trace self-check (NO_LOCAL_TRACE_CHECKLIST.md) on the WHOLE gold as it reads in the variant (the correct gold was
checked the same way first; it shows none of the patterns):
 T1 absent: `value` is read in the loop bound, in charAt, and is the returned field on the plain path; `searchChars` decides the
    enclosure through `searchChars.indexOf(ch) >= 0`; no parameter is read only in a check.
 T2 absent: `buf` is returned on the enclosed path; `enclose` (literal false) is assigned in the loop's search-character branch
    and decides the return; `i` advances; `ch` is written; the double-quote branch writes the extra quote that the enclosed
    field returns (e.g. "a\"b,c"), so no branch is dead or duplicated, and nothing is frozen.
 T3 absent: the only set the gold's text names is searchChars ("the delimiter and the line break characters"), and it is handled
    as a whole by one generic test; the double quote is named only as the character written twice inside the enclosing quotes,
    which the body does; the two enclosing quotes are both written (front and back); no format or standard is named.
 T4 absent: the javadoc's concrete phrases ("the value itself", "the value enclosed in double quotes", "each double quote of the
    value written twice" inside the enclosing quotes) are each produced by a path of the body; "not null" clauses are caller
    preconditions.
"""

SEU = "src/java/org/apache/commons/lang/StringEscapeUtils.java"
DU = "src/java/org/apache/commons/lang/time/DateUtils.java"
TSS = "src/java/org/apache/commons/lang/builder/ToStringStyle.java"
SB = "src/java/org/apache/commons/lang/text/StrBuilder.java"
FDF = "src/java/org/apache/commons/lang/time/FastDateFormat.java"
AU = "src/java/org/apache/commons/lang/ArrayUtils.java"

GOLD_TEXT = r'''/**
 * <p>Returns a value as a field of a delimited line of text.</p>
 *
 * <p>The field is the value itself, or the value enclosed in double
 * quotes with each double quote of the value written twice.</p>
 *
 * @param value  the value to write as a field, not null
 * @param searchChars  the delimiter and the line break characters,
 *  not null
 * @return the field for the value
 */
public static String toField(String value, String searchChars) {
    StringBuffer buf = new StringBuffer(value.length() + 2);
    boolean enclose = false;
    for (int i = 0; i < value.length(); i++) {
        char ch = value.charAt(i);
        if (ch == '"') {
            buf.append(ch);
            enclose = true;
        } else if (searchChars.indexOf(ch) >= 0) {
            enclose = true;
        }
        buf.append(ch);
    }
    if (enclose) {
        return "\"" + buf.toString() + "\"";
    }
    return value;
}'''

HOP1 = r'''/**
 * <p>Returns a value as a field of a comma separated line of text.</p>
 *
 * @param value  the value to write as a field, not null
 * @return the field for the value
 */
public static String lineFieldOf(String value) {
    return ToStringStyle.fieldFor(value, ',');
}'''

HOP2 = r'''/**
 * <p>Returns a value as a field of a line of text whose fields are
 * separated by the given delimiter.</p>
 *
 * <p>The characters searched for in the value are the delimiter and
 * the two line break characters.</p>
 *
 * @param value  the value to write as a field, not null
 * @param delimiter  the character that separates the fields of a line
 * @return the field for the value
 */
public static String fieldFor(String value, char delimiter) {
    return StrBuilder.fieldText(value, delimiter + "\r\n");
}'''

HOP3 = r'''/**
 * <p>Returns a value as a field of a delimited line of text.</p>
 *
 * <p>An empty value gives an empty field.</p>
 *
 * @param value  the value to write as a field, not null
 * @param searchChars  the delimiter and the line break characters,
 *  not null
 * @return the field for the value
 */
public static String fieldText(String value, String searchChars) {
    if (value.length() == 0) {
        return value;
    }
    return FastDateFormat.textAsField(value, searchChars);
}'''

HOP4 = r'''/**
 * <p>Returns a non-empty value as a field of a delimited line of
 * text.</p>
 *
 * @param value  the value to write as a field, not null or empty
 * @param searchChars  the delimiter and the line break characters,
 *  not null
 * @return the field for the value
 */
public static String textAsField(String value, String searchChars) {
    return ArrayUtils.toField(value, searchChars);
}'''

DESIGN = {
 "instance": "Lang-46", "project": "Lang", "bug_id": 46, "seed": 4967,
 "src_root": "src/java", "test_root": "src/test",
 "facade": {"file": SEU, "class": "org.apache.commons.lang.StringEscapeUtils", "method": "escapeCsv", "near_line": 725},
 "trigger": {"existing": True, "test_file": "src/test/org/apache/commons/lang/StringEscapeUtilsTest.java",
             "test_class": "org.apache.commons.lang.StringEscapeUtilsTest", "test_method": "testEscapeCsvString"},
 "expected_signature": "but was:<[foo\"bar]>",
 "gold": {"method": "toField", "text": GOLD_TEXT,
          "fault": {"old": "            if (ch == '\"') {\n"
                           "                buf.append(ch);\n"
                           "                enclose = true;\n"
                           "            } else if (searchChars.indexOf(ch) >= 0) {",
                    "new": "            if (ch == '\"') {\n"
                           "                buf.append(ch);\n"
                           "            } else if (searchChars.indexOf(ch) >= 0) {"}},
 "chain": {
   "facade_body": "if (str == null) {\n            return null;\n        }\n"
                  "        return org.apache.commons.lang.time.DateUtils.lineFieldOf(str);",
   "lie": "The characters of the value are visited from the last to the first, each one being inserted at the front of "
          "the buffer that holds the field.",
   "hops": [
     {"file": DU, "class": "org.apache.commons.lang.time.DateUtils", "method": "lineFieldOf",
      "imports": ["org.apache.commons.lang.builder.ToStringStyle"], "text": HOP1},
     {"file": TSS, "class": "org.apache.commons.lang.builder.ToStringStyle", "method": "fieldFor",
      "imports": ["org.apache.commons.lang.text.StrBuilder"], "text": HOP2},
     {"file": SB, "class": "org.apache.commons.lang.text.StrBuilder", "method": "fieldText",
      "imports": ["org.apache.commons.lang.time.FastDateFormat"], "text": HOP3},
     {"file": FDF, "class": "org.apache.commons.lang.time.FastDateFormat", "method": "textAsField",
      "imports": ["org.apache.commons.lang.ArrayUtils"], "text": HOP4},
     {"file": AU, "class": "org.apache.commons.lang.ArrayUtils", "method": "toField", "imports": [], "gold": True},
   ],
 },
 "evidence": ["org.apache.commons.lang.StringEscapeUtils::escapeCsv",
              "org.apache.commons.lang.StringEscapeUtils::unescapeCsv",
              "org.apache.commons.lang.text.StrTokenizer::getCSVInstance"],
 "ownership_reason": "Only the gold visits the characters of the value; hop 1 places the comma, hop 2 assembles the search "
                     "characters (the delimiter and CR, LF), hop 3 returns an empty value as it is, hop 4 passes the value "
                     "along. The double-quote branch precedes the search-character test, so no search set from above can make "
                     "a double quote enclose the field, and doubling the quotes before the gold only doubles them again; when the "
                     "gold does not enclose it returns the value and discards its buffer, so no caller can recover the field "
                     "without re-implementing it. The convention that a double quote forces enclosure is pinned outside the "
                     "gold: the facade's javadoc ('If the value contains a comma, newline or double quote, then the String "
                     "value is returned enclosed in double quotes'); the Writer overload escapeCsv(Writer, String) encloses "
                     "unless containsNone(str, CSV_SEARCH_CHARS) with CSV_SEARCH_CHARS = {',', '\"', CR, LF} "
                     "(testEscapeCsvWriter: \"foo\\\"bar\" -> \"\\\"foo\\\"\\\"bar\\\"\"); unescapeCsv reads a quoted field "
                     "whose content holds a double quote as escaped (testUnescapeCsvString, testUnescapeCsvWriter); "
                     "StrTokenizer.getCSVInstance's reader starts a quoted section at any double quote outside one, so an "
                     "unenclosed field holding a double quote does not read back (StrTokenizerTest::testBasicQuoted5, "
                     "testBasicQuoted3).",
 "ownership_tests": ["org.apache.commons.lang.StringEscapeUtilsTest::testEscapeCsvWriter",
                     "org.apache.commons.lang.StringEscapeUtilsTest::testUnescapeCsvString",
                     "org.apache.commons.lang.StringEscapeUtilsTest::testUnescapeCsvWriter",
                     "org.apache.commons.lang.text.StrTokenizerTest::testBasicQuoted3",
                     "org.apache.commons.lang.text.StrTokenizerTest::testBasicQuoted5"],
 "compensating": {
   "chain": [
     {"file": TSS, "old": r'return StrBuilder.fieldText(value, delimiter + "\r\n");',
      "new": r'return StrBuilder.fieldText(value, delimiter + "\"\r\n");',
      "why": "hop 2 adds the double quote to the search characters"},
     {"file": FDF, "old": "return ArrayUtils.toField(value, searchChars);",
      "new": r'return ArrayUtils.toField(org.apache.commons.lang.StringUtils.replace(value, "\"", "\"\""), searchChars);',
      "why": "hop 4 passes the value with its double quotes already doubled"},
     {"file": DU, "old": "return ToStringStyle.fieldFor(value, ',');",
      "new": "return ToStringStyle.fieldFor(value, '\"');",
      "why": "hop 1 passes the double quote as the delimiter"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 4967 (mr_lib preview, target org/apache/commons/lang/StringEscapeUtils.java): "
               "time.DateUtils (hop 1), builder.ToStringStyle (hop 2), text.StrBuilder (hop 3), time.FastDateFormat (hop 4), "
               "ArrayUtils (hop 5, gold). All five are public classes in which a static method compiles (ToStringStyle is "
               "abstract, which does not affect a static method); none was skipped. The draw note for hop 5 records that the "
               "package-distinctness heuristic was relaxed because the pool had two candidates left; the draw itself was "
               "used unchanged. The facade calls hop 1 by its fully-qualified name; each hop imports the next host.",
}
