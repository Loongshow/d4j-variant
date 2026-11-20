"""Main run JacksonCore-5 (C10 recipe on the fixed checkout of Defects4J JacksonCore-5; the real bug modified JsonPointer, and the
facade is the pool's only candidate, JsonPointer.compile(String), called by all four TestJsonPointer tests).

The facade keeps its two argument checks (null/empty input -> EMPTY; no leading slash -> IllegalArgumentException) and delegates
to a five-hop chain drawn with the instance seed 8341 (mr_lib preview, n=5, draw order, no substitution):
  hop 1 json.UTF8StreamJsonParser.parsePointer      pass-through
  hop 2 JsonGenerator.linkSegments                  fold: walks the expression, ends the first segment at the next slash (a
                                                    tilde and the character after it stay in one segment, as in _parseTail),
                                                    links it to the pointer for the rest of the expression (recursion), EMPTY
                                                    at the end
  hop 3 json.WriterBasedJsonGenerator.propertyNameAt placement: the first segment lies between the leading slash and `end`
  hop 4 json.UTF8JsonGenerator.segmentProperty      pass-through
  hop 5 json.ReaderBasedJsonParser.segmentName      GOLD: the per-character decode of one segment (~0 -> '~', ~1 -> '/', any
                                                    other tilde pair kept as is, a trailing tilde kept)
The chain performs exactly the original computation (_parseTail + _parseQuotedTail + _appendEscape): same segment boundaries
(including the original's '~/' behaviour), same full-string suffixes, same decoded names, same EMPTY terminator; the index is
still parsed by the JsonPointer constructor. Only JsonGenerator shares JsonPointer's package, so only it can call the protected
constructor and EMPTY: the draw put it at hop 2, where the fold belongs. The original protected helpers _parseTail,
_parseQuotedTail and the private _appendEscape stay in JsonPointer unchanged (no pre_edits): they are the class's own parsing
helpers and the external production pin of the escape convention.

Fault (omission in the gold): the '~1' -> '/' rule is dropped, so an escaped slash is kept as the two characters "~1" (it falls
into the branch that keeps unknown tilde pairs). After the omission the gold still reads as a complete decoder for ordinary
input (it decodes ~0 and copies everything else). Trigger: the EXISTING TestJsonPointer::testQuotedPath ("/w~1out/til~0de/a~1b"):
getMatchingProperty() expected "w/out", got "w~1out". It is the only test in the suite with a tilde in a pointer (and the only
users of JsonPointer are the four TestJsonPointer tests), so G5 holds; testSimplePath, testLongNumbers, testWonkyNumber173 stay
green.

The gold's javadoc states the idiomatic contract (escape sequences replaced by the characters they stand for, other characters
copied) and names no particular sequence (quiet). External pins: JsonPointer._appendEscape ('0' -> '~', '1' -> '/') and
_parseQuotedTail (production code doing the same step), the class javadoc's link to the JSON Pointer specification, and the
trigger's own expectations.

Single owner: only the gold reads the characters of a segment. A caller cannot pre-filter: the boundaries, the suffix strings
(toString, asserted by every TestJsonPointer test) and the offsets handed down are all computed on the raw expression, so
decoding '~1' before the gold either splits a segment (hops 1-2) or shifts the offsets (hops 3-4); and a same-length input
rewrite cannot make the omitted decoder emit '/'. A caller cannot recover: the omitted decoder maps both "~1" and "~01" to "~1",
so a post-hoc replace("~1", "/") at hops 2-4 turns "~01" (which stands for "~1": _appendEscape, RFC 6901 section 4) into "/" --
exactly the double-decoding the specification warns against; it passes the suite only because no test has "~01", and it
contradicts the documented decode. Declared G9 alternatives (all pre-decodings, none absorbs): hop 1, hop 3 and hop 4 replace
"~1" by "/" in the expression before the chain goes on.

Recorded bypasses (not competing repairs):
 B-0 facade `return _parseTail(input);` (the pre-chain parse) or hop 2 `return JsonPointer._parseTail(input);` (same package):
     the original implementation replaces the chain; hops 3-5 (resp. all hops) become dead.
 B-1 hop 4 (or 3/2) re-implements the omitted step around the gold with a same-length sentinel:
     `return ReaderBasedJsonParser.segmentName(input.replace("~1", "~\\0"), start, end).replace("~\\0", "/");`
     a second implementation of the '~1' rule outside the gold. Checked in scratch on the variant: full suite clean; it gives
     "~/" for "/~~1" where _appendEscape/_parseTail give "~~1" (and it misreads a literal NUL after a tilde).
 B-2 hop 2/3/4 post-hoc `.replace("~1", "/")` on the gold's result. Checked in scratch on the variant: full suite clean, but
     "/~01" yields "/" where the original parse (and RFC 6901) yields "~1": the double decoding, inconsistent with the
     documented decode, so not a competing repair.
Builder checks (scratch, correct configuration): JsonPointer.compile and the untouched JsonPointer._parseTail agree (toString,
property, index, matches of every segment) on 28 inputs incl. "/", "//", "/~", "/a~/b", "/~/", "/~01", "/~~1", "/~2x/y",
"/~~~1/~0~0~"; variant full suite: only testQuotedPath fails."""

SRC = "src/main/java/com/fasterxml/jackson/core"
JP = f"{SRC}/JsonPointer.java"
H1 = f"{SRC}/json/UTF8StreamJsonParser.java"
H2 = f"{SRC}/JsonGenerator.java"
H3 = f"{SRC}/json/WriterBasedJsonGenerator.java"
H4 = f"{SRC}/json/UTF8JsonGenerator.java"
H5 = f"{SRC}/json/ReaderBasedJsonParser.java"

GOLD_TEXT = '''/**
 * Method for decoding the property name that a segment of a JSON Pointer
 * expression stands for: escape sequences in the segment are replaced by
 * the characters they stand for, other characters are copied as is.
 *
 * @param input JSON Pointer expression
 * @param start Offset of the first character of the segment
 * @param end Offset after the last character of the segment
 *
 * @return Property name of the segment
 */
public static String segmentName(String input, int start, int end)
{
    StringBuilder sb = new StringBuilder(end - start);
    for (int i = start; i < end; ++i) {
        char c = input.charAt(i);
        if (c == '~' && i + 1 < end) {
            c = input.charAt(++i);
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
    return sb.toString();
}'''

HOP1 = '''/**
 * Method for constructing the pointer instance that matches given
 * JSON Pointer expression, which starts with a slash.
 *
 * @param input JSON Pointer expression, starting with a slash ('/')
 *
 * @return Pointer instance for the expression
 */
public static JsonPointer parsePointer(String input)
{
    return JsonGenerator.linkSegments(input);
}'''

HOP2 = '''/**
 * Method for constructing the pointer instance for a JSON Pointer
 * expression that starts with a slash: the first segment runs from that
 * slash up to the next one (or to the end of the expression), and is
 * linked to the pointer for the rest of the expression. A tilde and the
 * character that follows it always stay within one segment.
 *
 * @param input JSON Pointer expression, starting with a slash ('/')
 *
 * @return Pointer instance for the expression
 */
public static JsonPointer linkSegments(String input)
{
    final int end = input.length();
    for (int i = 1; i < end; ++i) {
        char c = input.charAt(i);
        if (c == '/') {
            return new JsonPointer(input, WriterBasedJsonGenerator.propertyNameAt(input, i),
                    linkSegments(input.substring(i)));
        }
        if (c == '~') {
            ++i;
        }
    }
    return new JsonPointer(input, WriterBasedJsonGenerator.propertyNameAt(input, end), JsonPointer.EMPTY);
}'''

HOP3 = '''/**
 * Method for finding the property name of the first segment of a JSON
 * Pointer expression, the segment being made of the characters between
 * the leading slash and given end offset.
 *
 * @param input JSON Pointer expression, starting with a slash ('/')
 * @param end Offset of the slash that ends the first segment, or length
 *   of the expression if there is no such slash
 *
 * @return Property name of the first segment
 */
public static String propertyNameAt(String input, int end)
{
    return UTF8JsonGenerator.segmentProperty(input, 1, end);
}'''

HOP4 = '''/**
 * Method for finding the property name that a segment of a JSON Pointer
 * expression stands for.
 *
 * @param input JSON Pointer expression
 * @param start Offset of the first character of the segment
 * @param end Offset after the last character of the segment
 *
 * @return Property name of the segment
 */
public static String segmentProperty(String input, int start, int end)
{
    return ReaderBasedJsonParser.segmentName(input, start, end);
}'''

FACADE_BODY = r'''if ((input == null) || input.length() == 0) {
            return EMPTY;
        }
        if (input.charAt(0) != '/') {
            throw new IllegalArgumentException("Invalid input: JSON Pointer expression must start with '/': "+"\""+input+"\"");
        }
        return com.fasterxml.jackson.core.json.UTF8StreamJsonParser.parsePointer(input);'''

DESIGN = {
 "instance": "JacksonCore-5", "project": "JacksonCore", "bug_id": 5, "seed": 8341,
 "src_root": "src/main/java", "test_root": "src/test/java",
 "facade": {"file": JP, "class": "com.fasterxml.jackson.core.JsonPointer", "method": "compile", "near_line": 88},
 "trigger": {"existing": True, "test_file": "src/test/java/com/fasterxml/jackson/core/TestJsonPointer.java",
             "test_class": "com.fasterxml.jackson.core.TestJsonPointer", "test_method": "testQuotedPath"},
 "expected_signature": "but was:<w[~1]out>",
 "gold": {"method": "segmentName", "text": GOLD_TEXT,
          "fault": {"old": "                if (c == '0') {\n"
                           "                    c = '~';\n"
                           "                } else if (c == '1') {\n"
                           "                    c = '/';\n"
                           "                } else {",
                    "new": "                if (c == '0') {\n"
                           "                    c = '~';\n"
                           "                } else {"}},
 "chain": {
   "facade_body": FACADE_BODY,
   "lie": "The expression is read once from its last character back to its first, and every pointer built on the way is kept "
          "in a shared cache keyed by its remaining expression, so that later calls with the same tail reuse that instance.",
   "hops": [
     {"file": H1, "class": "com.fasterxml.jackson.core.json.UTF8StreamJsonParser", "method": "parsePointer",
      "imports": [], "text": HOP1},
     {"file": H2, "class": "com.fasterxml.jackson.core.JsonGenerator", "method": "linkSegments",
      "imports": ["com.fasterxml.jackson.core.json.WriterBasedJsonGenerator"], "text": HOP2},
     {"file": H3, "class": "com.fasterxml.jackson.core.json.WriterBasedJsonGenerator", "method": "propertyNameAt",
      "imports": [], "text": HOP3},
     {"file": H4, "class": "com.fasterxml.jackson.core.json.UTF8JsonGenerator", "method": "segmentProperty",
      "imports": [], "text": HOP4},
     {"file": H5, "class": "com.fasterxml.jackson.core.json.ReaderBasedJsonParser", "method": "segmentName",
      "imports": [], "gold": True},
   ],
 },
 "evidence": ["com.fasterxml.jackson.core.JsonPointer::_appendEscape",
              "com.fasterxml.jackson.core.JsonPointer::_parseQuotedTail",
              "com.fasterxml.jackson.core.JsonPointer::_parseTail"],
 "ownership_reason": "Only the segment decoder reads the characters of a segment; the facade, the pass-throughs, the placement "
                     "step and the fold hand down the raw expression and offsets computed on it. Once the decoder has kept an "
                     "escaped slash as the two characters '~1' the name is ambiguous ('~1' and '~01' both come out as '~1'), so no "
                     "caller can recover it: a post-hoc replace(\"~1\", \"/\") turns '~01', which stands for '~1', into '/' (the "
                     "double decoding RFC 6901 section 4 warns against; JsonPointer._appendEscape decodes '~01' as '~1'), "
                     "contradicting the documented decode. No caller can pre-filter: decoding '~1' in the expression before the "
                     "fold splits the segment and changes every suffix string (toString), and decoding it below the fold shifts "
                     "the offsets. The convention is pinned outside the gold by JsonPointer._appendEscape ('1' -> '/') and "
                     "_parseQuotedTail, the class javadoc's reference to the JSON Pointer specification, and the trigger's own "
                     "expectations ('w~1out' -> 'w/out', 'a~1b' -> 'a/b'); the other TestJsonPointer tests pin the boundaries, "
                     "suffix strings and plain names that the non-gold hops produce.",
 "ownership_tests": ["com.fasterxml.jackson.core.TestJsonPointer::testSimplePath",
                     "com.fasterxml.jackson.core.TestJsonPointer::testLongNumbers",
                     "com.fasterxml.jackson.core.TestJsonPointer::testWonkyNumber173"],
 "compensating": {
   "chain": [
     {"file": H1, "old": "        return JsonGenerator.linkSegments(input);",
      "new": "        return JsonGenerator.linkSegments(input.replace(\"~1\", \"/\"));",
      "why": "hop 1 decodes escaped slashes in the expression before the segments are linked"},
     {"file": H3, "old": "        return UTF8JsonGenerator.segmentProperty(input, 1, end);",
      "new": "        return UTF8JsonGenerator.segmentProperty(input.replace(\"~1\", \"/\"), 1, end);",
      "why": "hop 3 places the segment on the expression with escaped slashes decoded"},
     {"file": H4, "old": "        return ReaderBasedJsonParser.segmentName(input, start, end);",
      "new": "        return ReaderBasedJsonParser.segmentName(input.replace(\"~1\", \"/\"), start, end);",
      "why": "hop 4 hands the decoder the expression with escaped slashes decoded"},
   ],
 },
 "host_notes": "Hosts in draw order for seed 8341 (mr_lib preview, n=5, target com/fasterxml/jackson/core/JsonPointer.java): "
               "json.UTF8StreamJsonParser (hop 1), JsonGenerator (hop 2), json.WriterBasedJsonGenerator (hop 3), "
               "json.UTF8JsonGenerator (hop 4), json.ReaderBasedJsonParser (hop 5, gold). The checkout has exactly five classes "
               "of at least 1500 lines, so the draw exhausts the pool (the recipe relaxed its package-distinctness heuristics, as "
               "the preview notes) and n=6 has no further host. All five are public classes in which a static method compiles; "
               "none was skipped. JsonGenerator is abstract and is the only host in JsonPointer's package, so the fold that calls "
               "the protected JsonPointer constructor and EMPTY sits there (hop 2 by draw); hops 1, 3, 4, 5 use only public types "
               "(the json hosts import com.fasterxml.jackson.core.*). WriterBasedJsonGenerator is final; static methods are fine.",
}
