import json, os
D = os.path.dirname(os.path.abspath(__file__))
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
CSU = "src/main/java/org/apache/commons/lang3/CharSequenceUtils.java"
SB = "src/main/java/org/apache/commons/lang3/text/StrBuilder.java"
trigger_code = '''    @Test
    public void testCaseInsensitiveMatchOnBuilderContent() {
        final StrBuilder name = new StrBuilder("Quarterly-Report.TXT");
        final boolean hasWord = StringUtils.containsIgnoreCase(name, "report");
        final boolean hasExtension = StringUtils.endsWithIgnoreCase(name, ".txt");
        assertTrue(hasWord && hasExtension);
    }
'''
spec = {
 "iid": "NEW-R13-M9",
 "project": "Lang",
 "group": "NEW-R13-M9",
 "mechanism": "M9",
 "recipe": "R13",
 "tags": ["M9", "M15"],
 "tier": "EXPLORATORY",
 "kind": "new",
 "src_root": "src/main/java",
 "test_root": "src/test/java",
 "gold": {
  "class": "org.apache.commons.lang3.CharSequenceUtils",
  "method": "regionMatches",
  "file": CSU,
  "edits": [{"old": "            int index1 = thisStart;\n", "new": "            int index1 = start;\n"}]
 },
 "gold_key": "org.apache.commons.lang3.CharSequenceUtils::regionMatches",
 "fault_lines": ["int index1 = start;"],
 "context_edits": [],
 "decoys": [
  {"class": "org.apache.commons.lang3.StringUtils", "method": "containsIgnoreCase", "file": SU},
  {"class": "org.apache.commons.lang3.text.StrBuilder", "method": "charAt", "file": SB}
 ],
 "entry_points": [
  "org.apache.commons.lang3.StringUtils::endsWithIgnoreCase",
  "org.apache.commons.lang3.StringUtils::endsWith"
 ],
 "evidence": [
  "org.apache.commons.lang3.CharSequenceUtils::regionMatches",
  "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsIgnoreCase_StringString",
  "org.apache.commons.lang3.StringUtilsStartsEndsWithTest::testEndsWithIgnoreCase",
  "org.apache.commons.lang3.StringUtilsStartsEndsWithTest::testStartsWithAny",
  "org.apache.commons.lang3.text.StrBuilderTest::testCharAt"
 ],
 "ownership_reason": (
  "CharSequenceUtils.regionMatches owns the fault. Its javadoc defines thisStart as 'the index to start on the cs CharSequence' and "
  "start as 'the index to start on the substring CharSequence', and its own String branch forwards both unchanged to "
  "String.regionMatches(ignoreCase, thisStart, substring, start, length). Its non-String branch, taken whenever cs or substring is not a "
  "String (here the trigger's StrBuilder), initialises the cs cursor index1 from start instead of thisStart, so thisStart is never read "
  "on that branch and the substring is always compared with cs from offset start (0 for every caller). Both conjuncts of the trigger call "
  "it with thisStart > 0 and start == 0: containsIgnoreCase passes its loop index i, and endsWithIgnoreCase -> endsWith passes "
  "strOffset = str.length() - suffix.length(); both therefore compare 'report' / '.txt' with the leading characters of "
  "'Quarterly-Report.TXT' and return false, so the boolean assertion fails. The competing suspects are correct: the caller code does not "
  "depend on the CharSequence type, and the same callers with String arguments (String branch, which honours thisStart) pass "
  "StringUtilsEqualsIndexOfTest::testContainsIgnoreCase_StringString and StringUtilsStartsEndsWithTest::testEndsWithIgnoreCase; "
  "StrBuilder.charAt is covered by StrBuilderTest::testCharAt, and builder inputs already work on the non-String branch when "
  "thisStart == start == 0 (StringUtilsStartsEndsWithTest::testStartsWithAny with a StrBuilder). Restoring index1 = thisStart repairs both "
  "conjuncts; no one-line change to a single caller or to StrBuilder repairs both."),
 "ownership_tests": [
  "org.apache.commons.lang3.StringUtilsEqualsIndexOfTest::testContainsIgnoreCase_StringString",
  "org.apache.commons.lang3.StringUtilsStartsEndsWithTest::testEndsWithIgnoreCase",
  "org.apache.commons.lang3.StringUtilsStartsEndsWithTest::testStartsWithAny",
  "org.apache.commons.lang3.text.StrBuilderTest::testCharAt"
 ],
 "trigger": {
  "test_file": "src/test/java/org/apache/commons/lang3/StringUtilsStartsEndsWithTest.java",
  "test_class": "org.apache.commons.lang3.StringUtilsStartsEndsWithTest",
  "test_method": "testCaseInsensitiveMatchOnBuilderContent",
  "imports": [],
  "code": trigger_code
 },
 "extra_tests": [],
 "expected_signature": "junit.framework.AssertionFailedError",
 "compensating": [
  {"file": SU,
   "old": "            if (CharSequenceUtils.regionMatches(str, true, i, searchStr, 0, len)) {",
   "new": "            if (CharSequenceUtils.regionMatches(str.toString(), true, i, searchStr.toString(), 0, len)) {",
   "why": "one-line decoy edit: containsIgnoreCase compares String copies (String branch of regionMatches)"},
  {"file": SU,
   "old": "        for (int i = 0; i <= max; i++) {\n            if (CharSequenceUtils.regionMatches(str, true, i, searchStr, 0, len)) {",
   "new": "        for (int i = max; i >= 0; i--) {\n            if (CharSequenceUtils.regionMatches(str, true, i, searchStr, 0, len)) {",
   "why": "one-line decoy edit: containsIgnoreCase scans candidate offsets from the end"},
  {"file": SU,
   "old": "        return CharSequenceUtils.regionMatches(str, ignoreCase, strOffset, suffix, 0, suffix.length());",
   "new": "        return CharSequenceUtils.regionMatches(str.toString(), ignoreCase, strOffset, suffix.toString(), 0, suffix.length());",
   "why": "one-line entry-chain edit: endsWith compares String copies (String branch of regionMatches)"},
  {"file": SB,
   "old": "        if (index < 0 || index >= length()) {\n            throw new StringIndexOutOfBoundsException(index);\n        }\n        return buffer[index];",
   "new": "        if (index < 0 || index >= length()) {\n            throw new StringIndexOutOfBoundsException(index);\n        }\n        return toString().charAt(index);",
   "why": "one-line decoy edit: StrBuilder.charAt reads through the String form of the builder"}
 ]
}
json.dump(spec, open(os.path.join(D, "spec.json"), "w"), indent=1)
print("written")
