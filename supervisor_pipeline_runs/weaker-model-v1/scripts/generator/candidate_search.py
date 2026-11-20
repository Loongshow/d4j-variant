"""
Finds candidate (class, method) targets for the distance+lie interaction
recipe, inside a real Defects4J checkout.

Encodes the lessons learned from hand-selecting three targets in this
project's own randomized cross-project experiment: several classes drawn
at random (org.joda.time.format.ISODateTimeFormat, org.joda.time.TimeOfDay)
turned out to have NO usable candidate, because every method's real
arithmetic was delegated out to other objects (a Chronology, a
DateTimeField) rather than being self-contained in the method's own body.
A method with nothing to inject a bug into directly is not a valid
candidate no matter how the file is chosen - this module's scoring exists
specifically to catch that before an LLM call or a human is asked to design
a bug for it.

Two-stage filter, both mechanical (no LLM):
  1. find_large_classes(source_root, min_lines) - real classes big enough
     for the confirmed discovery-cost effect (HANDOFF.md Section 11.1 found
     no effect below ~2000 lines, a real effect at ~2180 lines).
  2. score_candidate_methods(filepath) - within a class, rank public/public
     static methods by a self-containedness heuristic: real operators used
     directly in the method's own body, a body length in a workable range,
     and (checked separately, against the project's test sources) existing
     direct test coverage.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "trajectory-analysis"))
from callgraph import extract_methods_from_file  # noqa: E402

# Direct arithmetic/comparison/control-flow signal, counted only in text
# that isn't itself inside a nested method-call's argument list is hard to
# do precisely with regex; this is a deliberately coarse proxy, good enough
# to separate "mostly does its own compute" from "mostly hands off to
# something else" - not a precise AST analysis. Every candidate this module
# surfaces should still be read by a human (or handed to the LLM design
# step with the full body) before a bug is designed against it.
OPERATOR_RE = re.compile(r'(?<![=!<>])[+\-*/%](?!=)|[<>]=?(?!=)|==|!=')
CONTROL_FLOW_RE = re.compile(r'\b(if|for|while|switch)\s*\(')
# A body that is essentially one statement calling out and returning -
# "return foo(...);" or "foo(...); return;" with nothing else of substance -
# has nothing of its own to inject a bug into.
PURE_DELEGATE_RE = re.compile(
    r'^\s*\{\s*return\s+[A-Za-z_][A-Za-z0-9_.]*\([^;]*\)\s*;\s*\}\s*$', re.DOTALL
)


def find_large_classes(source_root, min_lines=1500):
    """Real .java files under source_root with at least min_lines lines."""
    results = []
    for f in glob.glob(f"{source_root}/**/*.java", recursive=True):
        try:
            n = sum(1 for _ in open(f, encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        if n >= min_lines:
            results.append((f, n))
    results.sort(key=lambda x: -x[1])
    return results


def _method_own_signal(body_lines_after_header):
    text = "\n".join(body_lines_after_header)
    operators = len(OPERATOR_RE.findall(text))
    control_flow = len(CONTROL_FLOW_RE.findall(text))
    return operators, control_flow


def score_candidate_methods(filepath, min_body_lines=4, max_body_lines=50, require_static=False):
    """
    Returns a list of dicts, one per public/public-static method in
    filepath, ranked by a self-containedness score (higher = more real,
    directly-owned computation; a pure passthrough scores ~0 and should be
    filtered out by the caller before spending an LLM call or human review
    on it).

    require_static=True restricts to methods whose header contains
    'static' - needed by the two-file chain recipe (generate_chain.py),
    where both hops are extracted as static helper methods with no access
    to instance state, so only a genuinely static (or state-independent)
    original method can be safely relocated into two other classes.
    """
    methods = extract_methods_from_file(filepath)
    scored = []
    for m in methods:
        header_line = m["body"].split("\n")[0]
        if "public" not in header_line:
            continue
        if require_static and "static" not in header_line:
            continue
        n_lines = m["end_line"] - m["start_line"]
        if n_lines < min_body_lines or n_lines > max_body_lines:
            continue
        if PURE_DELEGATE_RE.match(m["body"].strip()):
            continue
        body_after_header = m["body"].split("\n")[1:]
        operators, control_flow = _method_own_signal(body_after_header)
        # crude delegation-ratio proxy: how many distinct qualified calls
        # (obj.method(...)) appear, versus the method's own operator count -
        # a method dominated by calls to other objects with few operators of
        # its own is exactly the TimeOfDay/ISODateTimeFormat failure mode.
        qualified_calls = len(re.findall(r'[A-Za-z_][A-Za-z0-9_]*\.[a-zA-Z_][A-Za-z0-9_]*\s*\(', "\n".join(body_after_header)))
        self_containedness = operators + control_flow - 0.5 * qualified_calls
        scored.append({
            "name": m["name"],
            "start_line": m["start_line"],
            "end_line": m["end_line"],
            "n_lines": n_lines,
            "operators": operators,
            "control_flow": control_flow,
            "qualified_calls": qualified_calls,
            "self_containedness": self_containedness,
            "body": m["body"],
        })
    scored.sort(key=lambda x: -x["self_containedness"])
    return scored


def file_covers_method(filepath, method_name):
    """
    True if method_name appears as a call directly inside filepath itself.

    Distinct from has_direct_test_coverage(method_name, test_root), which
    checks an entire directory SUBTREE - the two look similar but are NOT
    interchangeable. Passing a single file's own directory as test_root to
    has_direct_test_coverage (as an attempt to check "does this ONE file
    cover the method") silently checks that file's whole recursive subtree
    instead, which for a nested Maven test layout (e.g. Lang3's
    src/test/java/org/apache/commons/lang3/**) very often includes an
    unrelated sibling test class that happens to cover the method - a real,
    confirmed bug (found via a live end-to-end run on Lang's NumberUtils:
    it silently picked LocaleUtilsTest.java, which never itself mentions
    createBigInteger, as the "covering" test file, because NumberUtilsTest.
    java sits in a subdirectory beneath it - producing real collateral test
    failures once the bug was applied). Use this function whenever the
    question is about one specific file.
    """
    pattern = re.compile(r'\b' + re.escape(method_name) + r'\s*\(')
    try:
        text = open(filepath, encoding="utf-8", errors="ignore").read()
    except Exception:
        return False
    return bool(pattern.search(text))


def has_direct_test_coverage(method_name, test_root):
    """True if method_name appears as a call anywhere under test_root."""
    pattern = re.compile(r'\b' + re.escape(method_name) + r'\s*\(')
    for f in glob.glob(f"{test_root}/**/*.java", recursive=True):
        try:
            text = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if pattern.search(text):
            return True
    return False


if __name__ == "__main__":
    import sys
    source_root = sys.argv[1]
    test_root = sys.argv[2] if len(sys.argv) > 2 else None
    classes = find_large_classes(source_root, min_lines=1500)
    print(f"{len(classes)} classes >= 1500 lines")
    for f, n in classes[:5]:
        print(f"\n=== {f} ({n} lines) ===")
        candidates = score_candidate_methods(f)
        for c in candidates[:5]:
            covered = has_direct_test_coverage(c["name"], test_root) if test_root else None
            print(f"  {c['name']}  score={c['self_containedness']:.1f} "
                  f"ops={c['operators']} qcalls={c['qualified_calls']} "
                  f"lines={c['n_lines']} tested={covered}")
