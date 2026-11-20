"""
Applies a BugDesign to a real checkout and empirically validates it via
real `defects4j compile`/`test` - the same gate this whole project has used
by hand throughout (HANDOFF.md Section 6.2/8): every artifact must pass
real compilation and a real, deterministic 3x-repeated failure before it is
trusted, regardless of how confident the design step (human or LLM) was.

If validation fails, this module returns a structured failure reason that
the caller can feed back into llm_design.design_bug's retry_feedback, so
the LLM gets one real, specific signal about what went wrong rather than
being asked to guess again blind.
"""
import os
import re
import shutil
import subprocess


class ValidationResult:
    def __init__(self, ok, stage, detail):
        self.ok = ok
        self.stage = stage      # "baseline" | "compile" | "deterministic_fail" | "collateral"
        self.detail = detail

    def __repr__(self):
        return f"ValidationResult(ok={self.ok}, stage={self.stage!r}, detail={self.detail[:200]!r})"


def read_text_smart(path):
    """Read a file, detecting CRLF vs LF so callers can preserve it on write."""
    with open(path, "rb") as f:
        raw = f.read()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8")
    return text, crlf


def write_text_smart(path, text, crlf):
    data = text.replace("\r\n", "\n")
    if crlf:
        data = data.replace("\n", "\r\n")
    with open(path, "wb") as f:
        f.write(data.encode("utf-8"))


def apply_line_replacement(filepath, original_text, buggy_text):
    """
    Byte-safe (CRLF-preserving) exact-substring replacement. Raises
    ValueError if original_text isn't found exactly once - callers should
    treat that as a design failure to feed back to the LLM, not a bug in
    this function.
    """
    text, crlf = read_text_smart(filepath)
    count = text.count(original_text)
    if count == 0:
        raise ValueError(f"original_text not found verbatim in {filepath}")
    if count > 1:
        raise ValueError(f"original_text matches {count} locations in {filepath} - not unique")
    new_text = text.replace(original_text, buggy_text, 1)
    write_text_smart(filepath, new_text, crlf)


def insert_test_method(test_filepath, new_test_source, anchor_method_name=None):
    """
    Inserts new_test_source as a new method inside the test class, just
    before the class's final closing brace (or right after an anchor
    method if given, to keep related tests grouped - best-effort, falls
    back to end-of-class insertion if the anchor isn't found).
    """
    text, crlf = read_text_smart(test_filepath)
    lines = text.split("\n")
    insert_at = None
    if anchor_method_name:
        for i, line in enumerate(lines):
            if f" {anchor_method_name}(" in line and "public void" in line:
                depth = 0
                for j in range(i, len(lines)):
                    depth += lines[j].count("{") - lines[j].count("}")
                    if depth == 0 and "{" in "".join(lines[i:j + 1]):
                        insert_at = j + 1
                        break
                break
    if insert_at is None:
        # fall back: insert before the last closing brace in the file
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "}":
                insert_at = i
                break
    if insert_at is None:
        raise ValueError(f"could not find an insertion point in {test_filepath}")
    new_lines = lines[:insert_at] + ["", new_test_source, ""] + lines[insert_at:]
    write_text_smart(test_filepath, "\n".join(new_lines), crlf)


def run_defects4j(args, cwd, timeout=180):
    result = subprocess.run(
        ["defects4j"] + args, cwd=cwd, capture_output=True, text=True, timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


def clean_build_artifacts(checkout_dir):
    """
    Removes accumulated build output (build/, build-tests/, target/) before
    a compile, so a stale class file from a previous variant attempt can
    never masquerade as a fresh, correct compile result. This is the
    documented stale-build pitfall this project hit by hand several times
    before it became standard practice - defects4j's own `compile` does not
    always force a full rebuild on its own.
    """
    for name in ("build", "build-tests", "target"):
        path = os.path.join(checkout_dir, name)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)


def defects4j_compile(checkout_dir):
    clean_build_artifacts(checkout_dir)
    rc, out, err = run_defects4j(["compile"], cwd=checkout_dir)
    if rc != 0 or "BUILD FAILED" in out or "BUILD FAILED" in err:
        return ValidationResult(False, "compile", out + err)
    return ValidationResult(True, "compile", out)


def defects4j_test_one(checkout_dir, test_id, timeout=180):
    """test_id like 'org.pkg.SomeTests::testMethodName'. Returns (n_failures, raw_output)."""
    rc, out, err = run_defects4j(["test", "-t", test_id], cwd=checkout_dir, timeout=timeout)
    combined = out + err
    m = re.search(r"Failing tests:\s*(\d+)", combined)
    n_failures = int(m.group(1)) if m else None
    return n_failures, combined


def defects4j_test_full_suite(checkout_dir, timeout=1200):
    rc, out, err = run_defects4j(["test"], cwd=checkout_dir, timeout=timeout)
    combined = out + err
    m = re.search(r"Failing tests:\s*(\d+)", combined)
    n_failures = int(m.group(1)) if m else None
    fail_lines = [l for l in combined.split("\n") if l.strip().startswith("- ")]
    return n_failures, fail_lines, combined


def validate_control(checkout_dir, source_file_rel, test_file_rel, design,
                      test_method_name, expected_assertion_is_exception_free=True):
    """
    Full CONTROL validation sequence:
      1. baseline sanity: apply ONLY the new test (no bug) against the
         unmodified method, confirm it passes - catches a wrong hand-
         computed expected value before any bug is even involved.
      2. apply the bug inline, defects4j compile.
      3. run the new test 3x, confirm a deterministic FAIL with no
         exception in the failure output (a real requirement of this
         project's recipe - HANDOFF.md Section 6.2).
    Returns a list of ValidationResult, in order; caller should stop at the
    first failure and treat the whole design as needing revision.
    """
    results = []

    # Step 1: baseline (test only, no bug)
    insert_test_method(os.path.join(checkout_dir, test_file_rel), design.new_test_source,
                        anchor_method_name=None)
    comp = defects4j_compile(checkout_dir)
    results.append(comp)
    if not comp.ok:
        return results
    test_id = f"{_test_class_from_path(test_file_rel)}::{test_method_name}"
    n_fail, out = defects4j_test_one(checkout_dir, test_id)
    baseline_ok = (n_fail == 0)
    results.append(ValidationResult(baseline_ok, "baseline", out))
    if not baseline_ok:
        return results

    # Step 2: apply the bug
    apply_line_replacement(os.path.join(checkout_dir, source_file_rel),
                            design.original_line_text, design.buggy_line_text)
    comp2 = defects4j_compile(checkout_dir)
    results.append(comp2)
    if not comp2.ok:
        return results

    # Step 3: deterministic fail, 3x, no exception
    for i in range(3):
        n_fail, out = defects4j_test_one(checkout_dir, test_id)
        is_clean_value_mismatch = (
            n_fail == 1
            and "Exception" not in out.split("Failing tests:")[-1]
            and ("AssertionFailedError" in out or "ComparisonFailure" in out or "expected" in out.lower())
        )
        results.append(ValidationResult(is_clean_value_mismatch, "deterministic_fail",
                                         f"run {i+1}/3: n_fail={n_fail}\n{out[-1500:]}"))
        if not is_clean_value_mismatch:
            return results

    return results


def check_zero_collateral(checkout_dir, expected_test_id):
    n_fail, fail_lines, out = defects4j_test_full_suite(checkout_dir)
    if n_fail is None:
        return ValidationResult(False, "collateral", "could not parse full-suite output\n" + out[-1500:])
    only_expected = (n_fail == 1) and any(expected_test_id.split("::")[-1] in l for l in fail_lines)
    return ValidationResult(only_expected, "collateral", "\n".join(fail_lines) if fail_lines else "0 failures")


def get_baseline_full_suite_failures(checkout_dir, timeout=1200):
    """
    Runs the full suite against the checkout AS IT CURRENTLY STANDS (call
    this on a clean, unmodified checkout) and returns the set of failing
    test ids ("ClassName::methodName" - the same short form check_zero_
    collateral's fail_lines use). Some projects have real, pre-existing
    environment/date-dependent flakiness independent of any change this
    pipeline makes (e.g. Commons Lang's DateUtilsTest, confirmed elsewhere
    in this project via git-stash differential testing) - this baseline
    lets collateral checks correctly ignore that known noise instead of
    either wrongly blocking on it or silently ignoring genuinely NEW
    collateral by using too loose a threshold.

    timeout should be raised for slower-suited projects (confirmed live:
    Joda-Time's full suite genuinely exceeds the 1200s/20min default,
    unlike Commons Lang's) - this is a real per-project property, not a
    hang, so raise the budget rather than treat a timeout as a failure.
    """
    try:
        n_fail, fail_lines, out = defects4j_test_full_suite(checkout_dir, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"baseline full-suite run exceeded timeout={timeout}s - this project's suite may "
            f"genuinely need more time (confirmed live on Joda-Time); rerun with a larger "
            f"--full-suite-timeout."
        )
    if n_fail is None:
        raise RuntimeError("could not parse baseline full-suite output:\n" + out[-1500:])
    names = set()
    for line in fail_lines:
        m = re.search(r'-\s+([\w.$]+::\w+)', line)
        if m:
            names.add(m.group(1))
    return names


def check_collateral_against_baseline(checkout_dir, expected_test_id, baseline_failures, timeout=1200):
    """
    Like check_zero_collateral, but tolerates any failure already present
    in baseline_failures (known pre-existing flakiness) instead of
    requiring exactly one failure total. Fails only if a NEW failure -
    neither the expected trigger nor part of the pre-existing baseline -
    shows up. This is the check that should gate design ACCEPTANCE (fed
    back into a retry, like a compile or deterministic-fail failure),
    since a bug that happens to break some OTHER pre-existing test for the
    same real method is a design problem the LLM can fix by choosing
    different bug/input values - not just a warning to log after the fact.
    """
    try:
        n_fail, fail_lines, out = defects4j_test_full_suite(checkout_dir, timeout=timeout)
    except subprocess.TimeoutExpired:
        # A slow project's suite genuinely needing more than `timeout` is a
        # real property (confirmed live on Joda-Time), not a hang - but an
        # uncaught TimeoutExpired previously crashed the whole script with
        # no chance to retry/feed back. Surface it as an ordinary failed
        # ValidationResult instead, so the caller's retry loop (or a human)
        # can raise --full-suite-timeout and retry, rather than losing the
        # whole run (and, if inside a design retry loop, an already-valid
        # design) to an unhandled exception.
        return ValidationResult(
            False, "collateral",
            f"full-suite run exceeded timeout={timeout}s - this project's suite may genuinely "
            f"need more time; rerun with a larger --full-suite-timeout rather than treating this "
            f"as a bad design."
        )
    if n_fail is None:
        return ValidationResult(False, "collateral", "could not parse full-suite output\n" + out[-1500:])
    expected_short = expected_test_id.split("::")[-1]
    new_failures = []
    saw_expected = False
    for line in fail_lines:
        m = re.search(r'-\s+([\w.$]+::\w+)', line)
        name = m.group(1) if m else line.strip()
        if expected_short in line:
            saw_expected = True
            continue
        if name in baseline_failures:
            continue
        new_failures.append(line)
    ok = saw_expected and not new_failures
    detail = ("NEW (non-baseline, non-trigger) failures:\n" + "\n".join(new_failures)) if new_failures \
        else ("trigger test did not fail" if not saw_expected else "clean (only baseline + trigger)")
    return ValidationResult(ok, "collateral", detail)


def _test_class_from_path(test_file_rel):
    """tests/org/pkg/junit/FooTests.java -> org.pkg.junit.FooTests (Defects4J-classic layout)
    or src/test/java/org/pkg/FooTest.java -> org.pkg.FooTest (Maven layout)."""
    parts = test_file_rel.replace("\\", "/").split("/")
    if "junit" in parts or parts[0] == "tests":
        start = parts.index("tests") + 1 if "tests" in parts else 0
    elif "java" in parts:
        start = len(parts) - 1 - parts[::-1].index("java")
        start += 1
    else:
        start = 0
    cls = ".".join(parts[start:])
    return cls[:-5] if cls.endswith(".java") else cls


def reset_checkout(checkout_dir):
    """git checkout -- . ; assumes checkout_dir is already a clean git repo baseline
    aside from untracked Major/build artifacts, matching this project's established
    reset-between-variants pattern."""
    subprocess.run(["git", "checkout", "--", "."], cwd=checkout_dir, check=True)


def check_no_name_leak(test_root, names):
    """
    Confirms none of `names` (the new hop/delegate method names) appear
    anywhere in the test tree. A leaked name in test source would hand the
    agent a free textual anchor into the hidden implementation - the exact
    kind of accidental shortcut this project's mechanism analysis (HANDOFF.md
    Section 11.21) found matters more than raw discovery cost. Returns a
    ValidationResult; failure detail names which name leaked into which file.
    """
    import glob as _glob
    leaks = []
    for f in _glob.glob(f"{test_root}/**/*.java", recursive=True):
        try:
            text = open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for name in names:
            if re.search(r'\b' + re.escape(name) + r'\b', text):
                leaks.append(f"{name} appears in {f}")
    ok = not leaks
    return ValidationResult(ok, "no_name_leak", "\n".join(leaks) if leaks else "clean")


def fresh_checkout_reproduction(project, bug_id, source_patch_text, test_patch_text,
                                 tmp_checkout_dir, trigger_test_id, timeout=180, expected_n_fail=1):
    """
    The final, established manual gate this project has run by hand before
    packaging every variant (HANDOFF.md's fresh-checkout reproduction step):
    a completely independent `defects4j checkout`, with the variant's own
    patches applied via `git apply` (never copying files from the working
    checkout), recompiled and retested from scratch. This is what actually
    proves the packaged variant.patch/test.patch are self-contained and
    correct, independent of any incidental state left over in the checkout
    the design/build loop used.

    tmp_checkout_dir must not already exist (this function creates it via
    `defects4j checkout`). Returns a list of ValidationResult in order;
    caller should treat any non-ok entry as a packaging-blocking failure.
    """
    results = []
    rc, out, err = run_defects4j(
        ["checkout", "-p", project, "-v", f"{bug_id}f", "-w", tmp_checkout_dir], cwd=".", timeout=300,
    )
    checkout_ok = (rc == 0) and os.path.isdir(tmp_checkout_dir)
    results.append(ValidationResult(checkout_ok, "fresh_checkout", out + err))
    if not checkout_ok:
        return results

    for label, patch_text in (("source_patch", source_patch_text), ("test_patch", test_patch_text)):
        patch_path = os.path.join(tmp_checkout_dir, f".{label}.diff")
        with open(patch_path, "w") as f:
            f.write(patch_text)
        p = subprocess.run(["git", "apply", patch_path], cwd=tmp_checkout_dir,
                            capture_output=True, text=True)
        apply_ok = (p.returncode == 0)
        results.append(ValidationResult(apply_ok, f"fresh_apply_{label}", p.stdout + p.stderr))
        if not apply_ok:
            return results

    comp = defects4j_compile(tmp_checkout_dir)
    results.append(comp)
    if not comp.ok:
        return results

    n_fail, out2 = defects4j_test_one(tmp_checkout_dir, trigger_test_id, timeout=timeout)
    trigger_ok = (n_fail == expected_n_fail)
    results.append(ValidationResult(trigger_ok, "fresh_trigger_fail",
                                     f"expected n_fail={expected_n_fail}, got {n_fail}\n{out2[-1500:]}"))
    return results
