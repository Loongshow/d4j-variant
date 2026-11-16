"""G-cue-refutable probe (no LLM): on the CORRECT configuration (gold right), implant the defect that each decoy cue implies
and record the trigger failure and the suite result. A cue is refutable by evidence when the implied defect gives a different
trigger failure from the observed one, or breaks existing tests that pass in every shipped configuration."""
import json, os, re, subprocess, shutil, sys
sys.path.insert(0, "/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/cue-trust-v3/scripts")
import ct_lib as C
L = C.L
spec = json.load(open(sys.argv[1])); W = spec["work"]; B = f"{C.V3}/instances/{spec['instance_id']}/build"
NA = "source/org/jfree/chart/axis/NumberAxis.java"
implied = {
 "CD1 (getters read each other's flag)": [("        return this.autoRangeIncludesZero;", "        return this.autoRangeStickyZero;"),
                                          ("        return this.autoRangeStickyZero;", "        return this.autoRangeIncludesZero;")],
 "CD2 (include-zero getter inverted)": [("        return this.autoRangeIncludesZero;", "        return !this.autoRangeIncludesZero;")],
}
def sh(c): return C.sh(c, W, 3600)
out = {}
for name, edits in implied.items():
    L.reset(W); sh(["git", "apply", f"{B}/CORRECT/test.patch"]); sh(["git", "apply", f"{B}/CORRECT/variant.patch"])
    t, eol = L.read(W, NA)
    # apply simultaneously
    marks = []
    for i, (o, n) in enumerate(edits):
        assert t.count(o) == 1, o; t = t.replace(o, f"@@{i}@@")
    for i, (o, n) in enumerate(edits): t = t.replace(f"@@{i}@@", n)
    L.write(W, NA, t, eol)
    for d in ("build", "build-tests"): shutil.rmtree(os.path.join(W, d), ignore_errors=True)
    rc, o = sh(["defects4j", "compile"])
    rc, o = sh(["defects4j", "test", "-t", f"{spec['trigger']['test_class']}::{spec['trigger']['test_method']}"])
    ft = open(os.path.join(W, "failing_tests")).read().strip().splitlines()[:2]
    rc, o2 = sh(["defects4j", "test"]); fails = sorted(set(re.findall(r"^\s*-\s+(\S+::\S+)", o2, re.M)))
    out[name] = {"trigger": "\n".join(ft), "suite_failures": fails}
    print(name, json.dumps(out[name], indent=1), flush=True)
L.reset(W)
json.dump(out, open(os.path.join(os.path.dirname(sys.argv[1]), "..", "..", "construction", "agentC", "screen", "cue_refute_CT-CHART-03.json"), "w"), indent=1)
