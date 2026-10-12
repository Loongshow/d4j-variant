"""Writes the CT-LANG-01 spec (deterministic)."""
import json
V3 = "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3"
A = f"{V3}/construction/agentA"
SU = "src/main/java/org/apache/commons/lang3/StringUtils.java"
TF = "src/test/java/org/apache/commons/lang3/StringUtilsTest.java"
DECL = "final String separatorChars, final int max, final boolean preserveAllTokens"
NEUTRAL = "// the character based splitter does the work"
trigger_code = '''    @Test
    public void testSplitByWholeString_EmptySeparator() {
        final String input = "ab de fg";

        final String[] results = StringUtils.splitByWholeSeparator(input, "");
        assertEquals(3, results.length);
        assertEquals("ab", results[0]);
        assertEquals("de", results[1]);
        assertEquals("fg", results[2]);

        final String[] preserved = StringUtils.splitByWholeSeparatorPreserveAllTokens("ab  de", "");
        assertEquals(3, preserved.length);
        assertEquals("ab", preserved[0]);
        assertEquals("", preserved[1]);
        assertEquals("de", preserved[2]);

        final String[] unsplit = StringUtils.split(input, "");
        assertEquals(1, unsplit.length);
        assertEquals(input, unsplit[0]);
    }
'''
spec = {
 "instance_id": "CT-LANG-01",
 "project": "Lang",
 "stratum": "shallow",
 "family": "wrong argument: the whitespace branch forwards the caller's separator instead of null, so an empty separator reaches splitWorker as an empty character set and nothing is split",
 "work": f"{A}/work/Lang",
 "fresh": f"{A}/fresh/Lang",
 "src_root": "src/main/java",
 "classes_dir": "target/classes",
 "prod_files": [SU],
 "test_files": [TF],
 "gold": {
  "file": SU,
  "class": "org.apache.commons.lang3.StringUtils",
  "method": "splitByWholeSeparatorWorker",
  "orig": "            // Split on whitespace.\n            return splitWorker(str, null, max, preserveAllTokens);",
  "bug": "            // Split on whitespace.\n            return splitWorker(str, separator, max, preserveAllTokens);",
  "orig_line": "return splitWorker(str, null, max, preserveAllTokens);",
  "bug_line": "return splitWorker(str, separator, max, preserveAllTokens);"
 },
 "decoys": [
  {"file": SU, "class": "org.apache.commons.lang3.StringUtils", "method": "splitWorker", "decl": DECL,
   "note": "the 4-argument overload (String separatorChars, int max, boolean preserveAllTokens); its 3-argument char overload is not on the trigger path"}
 ],
 "entry": "StringUtils#splitByWholeSeparator(String,String) and #splitByWholeSeparatorPreserveAllTokens(String,String) -> splitByWholeSeparatorWorker -> splitWorker(String,String,int,boolean)",
 "comment_anchor": {"file": SU, "anchor_fault": "            // Split on whitespace.\n", "anchor_correct": "            // Split on whitespace.\n", "where": "after"},
 "levels": {
  "C0": {"cue": "neutral", "comment": NEUTRAL, "renames": []},
  "CG1": {"cue": "gold-rationalising", "comment": "// separator can only be null on this path", "renames": []},
  "CG2": {"cue": "gold-rationalising", "comment": "// an empty separator has been normalized to null by this point", "renames": []},
  "CD1": {"cue": "decoy-incriminating", "comment": NEUTRAL,
          "renames": [{"scope": "method", "file": SU, "method": "splitWorker", "decl": DECL, "map": {"separatorChars": "separator"}}]},
  "CD2": {"cue": "decoy-incriminating", "comment": NEUTRAL,
          "renames": [{"scope": "method", "file": SU, "method": "splitWorker", "decl": DECL, "map": {"separatorChars": "wholeSeparator"}}]}
 },
 "trigger": {
  "test_file": TF,
  "test_class": "org.apache.commons.lang3.StringUtilsTest",
  "test_method": "testSplitByWholeString_EmptySeparator",
  "imports": [],
  "code": trigger_code
 },
 "expected_signature": "expected:<3> but was:<1>",
 "assertion_class_regex": "AssertionFailedError",
 "compensating": [
  {"file": SU, "old": "        if (separatorChars == null) {\n            // Null separator means use whitespace",
   "new": "        if (separatorChars == null || separatorChars.length() == 0) {\n            // Null separator means use whitespace",
   "why": "one-line decoy edit: splitWorker treats an empty separatorChars like null (whitespace)"},
  {"file": SU, "old": "        if (separatorChars == null) {\n            // Null separator means use whitespace",
   "new": "        if (isEmpty(separatorChars)) {\n            // Null separator means use whitespace",
   "why": "one-line decoy edit: splitWorker whitespace branch guarded by isEmpty(separatorChars)"},
  {"file": SU, "old": "                if (separatorChars.indexOf(str.charAt(i)) >= 0) {",
   "new": "                if (separatorChars.length() == 0 ? Character.isWhitespace(str.charAt(i)) : separatorChars.indexOf(str.charAt(i)) >= 0) {",
   "why": "one-line decoy edit: the standard-case scan treats an empty separatorChars as whitespace"},
  {"file": SU, "old": "        } else if (separatorChars.length() == 1) {",
   "new": "        } else if (separatorChars.length() <= 1) {",
   "why": "one-line decoy edit: route an empty separatorChars into the single-character branch"},
  {"file": SU, "old": "        return splitByWholeSeparatorWorker( str, separator, -1, false ) ;",
   "new": "        return splitByWholeSeparatorWorker( str, isEmpty(separator) ? null : separator, -1, false ) ;",
   "why": "one-line entry-facade edit: splitByWholeSeparator(String,String) maps an empty separator to null"},
  {"file": SU, "old": "        return splitByWholeSeparatorWorker(str, separator, -1, true);",
   "new": "        return splitByWholeSeparatorWorker(str, isEmpty(separator) ? null : separator, -1, true);",
   "why": "one-line entry-facade edit: splitByWholeSeparatorPreserveAllTokens(String,String) maps an empty separator to null"}
 ],
 "marker_methods": [
  {"role": "gold", "file": SU, "method": "splitByWholeSeparatorWorker"},
  {"role": "decoy", "file": SU, "method": "splitWorker", "decl": DECL}
 ],
 "notes": ("Shallow stratum: the faulty line is 15 lines below the splitByWholeSeparatorWorker signature (14 before the shared comment line). "
           "The gold key StringUtils::splitByWholeSeparatorWorker is unique (no overloads) and has four production callers (the splitByWholeSeparator and "
           "splitByWholeSeparatorPreserveAllTokens facades). Its own code owns the empty-separator case (`separator == null || EMPTY.equals(separator)` "
           "followed by '// Split on whitespace.'). The fault forwards the caller's separator, so for an empty separator splitWorker receives \"\" and "
           "returns the input unsplit. Owner invariance: with the fault, splitByWholeSeparator(input, \"\") and split(input, \"\") make the identical call "
           "splitWorker(input, \"\", -1, false), and the trigger requires the first to split on whitespace and the second to keep the string whole, so no "
           "edit confined to splitWorker can satisfy both; the two facade assertions also block any single-facade fix. CG cues are comment-only false local "
           "facts (refuted by the condition two lines above). CD cues rename splitWorker's parameter separatorChars to a whole-separator name, inviting a "
           "comparison with the worker's null-or-empty check; the truth stays visible in the split/splitPreserveAllTokens javadocs ('A null separatorChars "
           "splits on whitespace'), splitWorker's own comment ('Null separator means use whitespace') and the trigger's split(input, \"\") assertion.")
}
json.dump(spec, open(f"{V3}/instances/CT-LANG-01/spec.json", "w"), indent=1)
print("wrote spec")
