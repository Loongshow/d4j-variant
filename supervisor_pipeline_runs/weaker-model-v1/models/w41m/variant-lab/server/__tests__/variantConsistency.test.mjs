import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  artifactMapFor,
  changedPrePatchLines,
  findJavaMethodLineSpans,
  parseUnifiedDiffTargets,
  readVariantRecord,
  variantArtifactConsistency,
} from "../variantLibrary.mjs";

/* --------------------------------------------------------------------- fixtures */

const JAVA_SOURCE = `package com.example;

public class Widget {

    private boolean removeGlobals;
    private boolean modifyCallSites;

    /**
     * Traverses a function.
     */
    private void traverseFunction(Node n) {
        collect(n);
        reconcile(n);
    }

    /**
     * Removes unreferenced arguments.
     *
     * @param fnScope the scope
     */
    private void removeUnreferencedFunctionArgs(Scope fnScope) {
        // A comment about the guard below.
        //
        // See https://example.invalid/issue/253
        if (!removeGlobals) {
            return;
        }
        doWork(fnScope);
    }

    private void doWork(Scope scope) {
        scope.apply();
    }
}
`;

function lineOf(needle) {
  const index = JAVA_SOURCE.split("\n").findIndex((line) => line.includes(needle));
  assert.notEqual(index, -1, `fixture must contain ${needle}`);
  return index + 1;
}

/** A minimal one-line edit whose diff context never names the enclosing method. */
function minimalGuardPatch(file = "src/com/example/Widget.java") {
  const guardLine = lineOf("if (!removeGlobals) {");
  const start = guardLine - 3;
  return [
    `--- a/${file}`,
    `+++ b/${file}`,
    `@@ -${start},7 +${start},7 @@`,
    "     // See https://example.invalid/issue/253",
    "     //",
    "     //",
    "-        if (!removeGlobals) {",
    "+        if (!removeGlobals && !modifyCallSites) {",
    "             return;",
    "         }",
    "         doWork(fnScope);",
    "",
  ].join("\n");
}

async function writeFixture(root, { faultMethod = "removeUnreferencedFunctionArgs", faultFile = "src/com/example/Widget.java", variantPatch, testPatch, triggerFile = "test/com/example/WidgetTest.java", report } = {}) {
  const variantId = "EXAMPLE-1-L10-001";
  const variantsRoot = path.join(root, "new_bug_variants");
  const variantDir = path.join(variantsRoot, "Example", "bug-1", "L10", variantId);
  await fs.mkdir(variantDir, { recursive: true });

  const checkoutRoot = path.join(root, "workspaces", "defects4j");
  const sourcePath = path.join(checkoutRoot, "Example-1", "fixed", faultFile);
  await fs.mkdir(path.dirname(sourcePath), { recursive: true });
  await fs.writeFile(sourcePath, JAVA_SOURCE);

  const manifest = {
    schema_version: "d4j-variant-manifest/v1",
    variant_id: variantId,
    source: {
      defects4j_project: "Example",
      defects4j_bug_id: 1,
      fixed_revision: "1f",
      artifact_path: `new_bug_variants/Example/bug-1/L10/${variantId}/`,
    },
    status: "validated",
    benchmark_eligible: true,
    reproducibility: { status: "passed" },
    reasoning: { level: "L10", unit_count: 10, changed_node: "guard widened" },
    fault: {
      locations: [{ class: "com.example.Widget", method: faultMethod, file: faultFile, production: true }],
      gold: { faulty_class: "com.example.Widget", faulty_method: faultMethod },
    },
    trigger: {
      test_id: "com.example.WidgetTest::testGuard",
      test_method: "testGuard",
      test_class: "com.example.WidgetTest",
      file: triggerFile,
    },
    artifacts: artifactMapFor(variantId),
  };
  const validation = {
    schema_version: "d4j-validation/v1",
    variant_id: variantId,
    status: "accepted",
    gate: {
      baseline_compile: { status: "pass" },
      baseline_trigger: { status: "pass" },
      variant_compile: { status: "pass" },
      variant_trigger_runs: [{ status: "expected_fail" }, { status: "expected_fail" }, { status: "expected_fail" }],
      deterministic: { status: "pass" },
      production_fault: { status: "pass" },
      gold_method_known: { status: "pass" },
    },
  };

  const defaultTestPatch = [
    `--- a/${triggerFile}`,
    `+++ b/${triggerFile}`,
    "@@ -10,3 +10,7 @@",
    " public class WidgetTest {",
    "+    public void testGuard() {",
    "+        assertEquals(1, subject.observable());",
    "+    }",
    " }",
    "",
  ].join("\n");

  await fs.writeFile(path.join(variantDir, "variant_manifest.json"), JSON.stringify(manifest, null, 2));
  await fs.writeFile(path.join(variantDir, "validation.json"), JSON.stringify(validation, null, 2));
  await fs.writeFile(path.join(variantDir, "variant.patch"), variantPatch ?? minimalGuardPatch(faultFile));
  await fs.writeFile(path.join(variantDir, "test.patch"), testPatch ?? defaultTestPatch);
  await fs.writeFile(path.join(variantDir, "reasoning_tree.yaml"), "unit_count: 10\n");
  await fs.writeFile(path.join(variantDir, "validation.log"), "testGuard expected failure 3/3\n");
  await fs.writeFile(
    path.join(variantDir, "variant_report.md"),
    report ?? "# Report\n\ntestGuard exercises Widget and the guard in removeUnreferencedFunctionArgs.\n",
  );
  await fs.writeFile(path.join(variantDir, "generation_trace.json"), JSON.stringify({ variant_id: variantId }));

  return { variantDir, checkoutRoot };
}

async function withTempRoot(run) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "d4j-consistency-"));
  try {
    return await run(root);
  } finally {
    await fs.rm(root, { recursive: true, force: true });
  }
}

function checkById(result, id) {
  return result.checks.find((check) => check.id === id);
}

/* -------------------------------------------------------------- diff parsing */

test("parses unified diff targets, hunk ranges and changed pre-patch lines", () => {
  const targets = parseUnifiedDiffTargets(minimalGuardPatch());
  assert.equal(targets.length, 1);
  assert.equal(targets[0].file, "src/com/example/Widget.java");
  assert.equal(targets[0].hunks.length, 1);
  const [hunk] = targets[0].hunks;
  assert.equal(hunk.removed_old_lines.length, 1);
  assert.deepEqual(changedPrePatchLines(hunk), hunk.removed_old_lines);
});

test("a pure-insertion hunk reports insertion anchors instead of removals", () => {
  const patch = ["--- a/A.java", "+++ b/A.java", "@@ -10,2 +10,3 @@", " one", "+inserted", " two", ""].join("\n");
  const [target] = parseUnifiedDiffTargets(patch);
  const [hunk] = target.hunks;
  assert.deepEqual(hunk.removed_old_lines, []);
  assert.deepEqual(hunk.insertion_anchors, [11]);
  assert.deepEqual(changedPrePatchLines(hunk), [11]);
});

test("ignores /dev/null targets and multiple files are parsed independently", () => {
  const patch = [
    "--- a/A.java",
    "+++ b/A.java",
    "@@ -1,1 +1,1 @@",
    "-a",
    "+b",
    "--- a/B.java",
    "+++ /dev/null",
    "--- a/C.java",
    "+++ b/C.java",
    "@@ -5,1 +5,1 @@",
    "-c",
    "+d",
    "",
  ].join("\n");
  const targets = parseUnifiedDiffTargets(patch);
  assert.deepEqual(targets.map((target) => target.file), ["A.java", "C.java"]);
});

/* ---------------------------------------------------------- method line spans */

test("resolves Java method line spans including the body", () => {
  const spans = findJavaMethodLineSpans(JAVA_SOURCE, "removeUnreferencedFunctionArgs");
  assert.equal(spans.length, 1);
  assert.ok(spans[0].start_line < lineOf("if (!removeGlobals) {"));
  assert.ok(spans[0].end_line > lineOf("doWork(fnScope);"));
});

test("returns no spans for an unknown or malformed method name", () => {
  assert.deepEqual(findJavaMethodLineSpans(JAVA_SOURCE, "noSuchMethod"), []);
  assert.deepEqual(findJavaMethodLineSpans(JAVA_SOURCE, "not a name"), []);
  assert.deepEqual(findJavaMethodLineSpans("", "doWork"), []);
});

/* ------------------------------------------------- F-3 regression: the real bug */

test("F-3: a minimal edit whose context never names the method is structurally verified as a PASS", async () => {
  await withTempRoot(async (root) => {
    const { variantDir, checkoutRoot } = await writeFixture(root);
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, { checkoutRoot });

    const methodCheck = checkById(result, "fault:variant-patch-method");
    assert.equal(methodCheck.status, "pass");
    assert.equal(methodCheck.verification_mode, "structural_checkout");
    assert.equal(result.ok, true);
    assert.equal(result.fully_verified, true);

    // The old brittle behaviour: the method name really is absent from the patch text.
    const patch = await fs.readFile(path.join(variantDir, "variant.patch"), "utf8");
    assert.ok(!patch.includes("removeUnreferencedFunctionArgs"), "fixture must reproduce the F-3 condition");
  });
});

test("context lines outside the method do not cause a failure", async () => {
  await withTempRoot(async (root) => {
    const { variantDir, checkoutRoot } = await writeFixture(root);
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, { checkoutRoot });
    const methodCheck = checkById(result, "fault:variant-patch-method");
    const spans = methodCheck.method_spans;
    const changed = methodCheck.changed_pre_patch_lines;
    assert.ok(changed.every((line) => line >= spans[0].start_line && line <= spans[0].end_line));
  });
});

/* -------------------------------------------- the checker must still catch errors */

test("a genuinely incorrect method association still HARD-fails", async () => {
  await withTempRoot(async (root) => {
    const { variantDir, checkoutRoot } = await writeFixture(root, { faultMethod: "traverseFunction" });
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, { checkoutRoot });
    const methodCheck = checkById(result, "fault:variant-patch-method");
    assert.equal(methodCheck.status, "fail");
    assert.equal(methodCheck.verification_mode, "structural_checkout");
    assert.ok(methodCheck.outside_lines.length > 0);
    assert.equal(result.ok, false);
  });
});

test("a patch editing a file other than the declared fault file HARD-fails", async () => {
  await withTempRoot(async (root) => {
    const { variantDir, checkoutRoot } = await writeFixture(root, {
      variantPatch: minimalGuardPatch("src/com/example/Other.java"),
    });
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, { checkoutRoot });
    const fileCheck = checkById(result, "fault:variant-patch-file");
    assert.equal(fileCheck.status, "fail");
    assert.ok(fileCheck.message.includes("src/com/example/Other.java"));
    assert.equal(result.ok, false);
  });
});

test("a test patch editing a file other than the declared trigger file HARD-fails", async () => {
  await withTempRoot(async (root) => {
    const { variantDir, checkoutRoot } = await writeFixture(root, {
      testPatch: [
        "--- a/test/com/example/UnrelatedTest.java",
        "+++ b/test/com/example/UnrelatedTest.java",
        "@@ -1,1 +1,2 @@",
        " x",
        "+    public void testGuard() {}",
        "",
      ].join("\n"),
    });
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, { checkoutRoot });
    assert.equal(checkById(result, "trigger:test-patch-file").status, "fail");
    assert.equal(result.ok, false);
  });
});

/* ------------------------------------------------- unverified is not a silent pass */

test("without a checkout the method association is UNVERIFIED, never an implicit pass", async () => {
  await withTempRoot(async (root) => {
    const { variantDir } = await writeFixture(root);
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, {});
    const methodCheck = checkById(result, "fault:variant-patch-method");
    assert.equal(methodCheck.status, "unverified");
    assert.equal(result.ok, true, "unverified must not be reported as an inconsistency");
    assert.equal(result.fully_verified, false, "but it must block strict-cohort readiness");
    assert.deepEqual(result.unverified, ["fault:variant-patch-method"]);
  });
});

test("without a checkout, a patch that does name its method falls back lexically", async () => {
  await withTempRoot(async (root) => {
    const { variantDir } = await writeFixture(root, {
      variantPatch: [
        "--- a/src/com/example/Widget.java",
        "+++ b/src/com/example/Widget.java",
        "@@ -20,3 +20,3 @@ private void removeUnreferencedFunctionArgs(Scope fnScope) {",
        "-        if (!removeGlobals) {",
        "+        if (!removeGlobals && !modifyCallSites) {",
        "             return;",
        "",
      ].join("\n"),
    });
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, {});
    const methodCheck = checkById(result, "fault:variant-patch-method");
    assert.equal(methodCheck.status, "pass");
    assert.equal(methodCheck.verification_mode, "lexical_fallback");
  });
});

/* ----------------------------------------- leakage-controlled triggers are allowed */

test("F-3: a leakage-controlled trigger that omits the owner class is INFO, not a failure", async () => {
  await withTempRoot(async (root) => {
    const { variantDir, checkoutRoot } = await writeFixture(root);
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, { checkoutRoot });

    const lexical = checkById(result, "lexical:test-patch-names-owner");
    assert.equal(lexical.status, "info");
    assert.equal(lexical.exposed, false);
    assert.equal(lexical.owner_class, "Widget");
    assert.equal(result.ok, true);
    assert.deepEqual(result.lexical_exposures, []);
    assert.equal(checkById(result, "fault:test-patch-owner"), undefined, "the old brittle check must be gone");
  });
});

test("a trigger that does name the owner class is recorded as a lexical exposure covariate", async () => {
  await withTempRoot(async (root) => {
    const { variantDir, checkoutRoot } = await writeFixture(root, {
      testPatch: [
        "--- a/test/com/example/WidgetTest.java",
        "+++ b/test/com/example/WidgetTest.java",
        "@@ -10,2 +10,4 @@",
        " public class WidgetTest {",
        "+    public void testGuard() { new Widget().observable(); }",
        " }",
        "",
      ].join("\n"),
    });
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, { checkoutRoot });
    const lexical = checkById(result, "lexical:test-patch-names-owner");
    assert.equal(lexical.status, "info");
    assert.equal(lexical.exposed, true);
    assert.deepEqual(result.lexical_exposures, ["lexical:test-patch-names-owner"]);
    assert.equal(result.ok, true, "lexical exposure is a covariate, not an inconsistency");
  });
});

test("the private variant report is still required to name the fault owner", async () => {
  await withTempRoot(async (root) => {
    const { variantDir, checkoutRoot } = await writeFixture(root, { report: "# Report\n\ntestGuard does something.\n" });
    const record = await readVariantRecord(variantDir);
    const result = await variantArtifactConsistency(record, { checkoutRoot });
    assert.equal(checkById(result, "fault:report-owner").status, "fail");
    assert.equal(result.ok, false);
  });
});
