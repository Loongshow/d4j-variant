import assert from "node:assert/strict";
import test from "node:test";

import {
  EVIDENCE_POLICY_VERSION,
  EVIDENCE_PROVENANCE,
  LEGACY_EVIDENCE_POLICY_VERSION,
  buildFailureEvidence,
  classifyEvidenceProvenanceText,
  evidenceFormattingEquivalent,
  evidencePolicyCompliance,
  evidencePolicyVersionForManifest,
  failureEvidencePolicy,
  normalizeFailureEvidence,
  screenEvidenceForPrivateMetadata,
  truncateFailureEvidence,
} from "../evidencePolicy.mjs";

function realDefects4jOutput({ testId = "org.example.FooTest::testBar", frames = 3 } = {}) {
  const frameLines = Array.from(
    { length: frames },
    (_, index) => `    at org.example.Foo.method${index}(Foo.java:${100 + index})`,
  ).join("\n");
  return [
    "Failing tests: 1",
    `  - ${testId}`,
    "",
    "Running ant (compile.tests).................................... OK",
    "Running ant (run.dev.tests)........................................ OK",
    "",
    `--- ${testId}`,
    "junit.framework.ComparisonFailure: expected:<[Second]ary> but was:<[Prim]ary>",
    frameLines,
  ].join("\n");
}

const HUMAN_SUMMARY = "ComparisonFailure in CategoryPlotTests.testGeneratedItemMetadata; no gold method appears.";

/* ---------------------------------------------------------------- provenance */

test("classifies real captured Defects4J output as machine generated", () => {
  assert.equal(classifyEvidenceProvenanceText(realDefects4jOutput()), "machine_generated");
});

test("classifies a minimal three-line JUnit failure as machine generated", () => {
  const minimal = [
    "--- org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests::testLegendItems",
    "junit.framework.ComparisonFailure: expected:<[Second]ary> but was:<[Prim]ary>",
    "    at org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests.testLegendItems(AbstractCategoryItemRendererTests.java:412)",
  ].join("\n");
  assert.equal(classifyEvidenceProvenanceText(minimal), "machine_generated");
});

test("classifies a one-line human summary as human authored even when it names a JUnit type", () => {
  assert.equal(classifyEvidenceProvenanceText(HUMAN_SUMMARY), "human_authored_summary");
  assert.equal(
    classifyEvidenceProvenanceText("AssertionFailedError in IntegrationTest.testX; no gold class or method appears."),
    "human_authored_summary",
  );
});

test("classifies absent evidence as empty", () => {
  assert.equal(classifyEvidenceProvenanceText(""), "empty");
  assert.equal(classifyEvidenceProvenanceText(null), "empty");
  assert.equal(classifyEvidenceProvenanceText("   \n  "), "empty");
});

/* -------------------------------------------------------------- normalization */

test("normalization is deterministic and removes machine-specific detail", () => {
  const raw =
    "Run at 2026-09-12T11:57:50Z in /tmp/run-1/workspace/Chart-1\r\n" +
    "[31mFailing tests: 1[0m\r\n" +
    "Running ant (compile)................................. OK\r\n" +
    "Time: 12.345 sec\r\n" +
    "org.jfree.chart.plot.CategoryPlot@1f2e3d4c\r\n" +
    "    at org.example.Foo.bar(Foo.java:10)   \r\n";
  const first = normalizeFailureEvidence(raw, { workspaceRoot: "/tmp/run-1/workspace", repoRoot: "/tmp" });
  const second = normalizeFailureEvidence(raw, { workspaceRoot: "/tmp/run-1/workspace", repoRoot: "/tmp" });

  assert.equal(first.text, second.text, "normalization must be deterministic");
  assert.ok(first.text.includes("<WORKSPACE>"));
  assert.ok(first.text.includes("<TIMESTAMP>"));
  assert.ok(first.text.includes("<DURATION>"));
  assert.ok(first.text.includes("@<OBJID>"));
  assert.ok(!first.text.includes("["), "ANSI escapes must be removed");
  assert.ok(!first.text.includes("\r"), "CR must be removed");
  assert.ok(!/\.{5,}/.test(first.text), "dot padding must be collapsed");
  assert.ok(!/[ \t]+\n/.test(first.text), "trailing whitespace must be stripped");
});

test("normalization preserves natural class, method and file identifiers", () => {
  const raw = "    at org.jfree.chart.plot.CategoryPlot.setRenderer(CategoryPlot.java:1234)";
  const { text } = normalizeFailureEvidence(raw, { workspaceRoot: "/w", repoRoot: "/r" });
  assert.ok(text.includes("CategoryPlot"));
  assert.ok(text.includes("setRenderer"));
  assert.ok(text.includes("CategoryPlot.java"));
});

test("normalization redacts private benchmark roots that survive path substitution", () => {
  const raw = "read /Users/someone/Honours/defects4j/new_bug_variants/Chart/bug-1/L10/X/variant.patch";
  const { text } = normalizeFailureEvidence(raw, { workspaceRoot: "", repoRoot: "" });
  assert.ok(!text.includes("new_bug_variants"));
  assert.ok(text.includes("<REDACTED_PATH>"));
});

/* ----------------------------------------------------------------- truncation */

test("truncation applies head and tail with an explicit marker", () => {
  const lines = Array.from({ length: 400 }, (_, index) => `line ${index}`);
  const result = truncateFailureEvidence(lines.join("\n"));
  assert.equal(result.truncated, true);
  assert.equal(result.original_line_count, 400);
  assert.equal(result.omitted_lines, 400 - failureEvidencePolicy.head_lines - failureEvidencePolicy.tail_lines);
  assert.ok(result.text.startsWith("line 0"));
  assert.ok(result.text.trimEnd().endsWith("line 399"), "the tail must be preserved");
  assert.ok(result.text.includes(failureEvidencePolicy.truncation_marker));
  assert.ok(result.final_line_count <= failureEvidencePolicy.max_lines + 1);
});

test("truncation leaves realistic-length output untouched", () => {
  const output = realDefects4jOutput();
  const result = truncateFailureEvidence(output);
  assert.equal(result.truncated, false);
  assert.equal(result.text, output);
  assert.equal(result.omitted_lines, 0);
});

test("truncation enforces the character budget by trimming the tail, never the head", () => {
  const long = Array.from({ length: 60 }, () => "x".repeat(400)).join("\n");
  const result = truncateFailureEvidence(long);
  assert.equal(result.truncated, true);
  assert.ok(result.final_char_count <= failureEvidencePolicy.max_chars);
  assert.ok(result.text.startsWith("x".repeat(400)), "the head must survive the character budget");
});

/* -------------------------------------------------------------------- records */

test("a captured machine output is selected over a manifest human summary", () => {
  const record = buildFailureEvidence({
    capturedText: realDefects4jOutput(),
    manifestText: HUMAN_SUMMARY,
    failingTestIdentifier: "org.example.FooTest::testBar",
    allowedTestCommand: "defects4j test -t org.example.FooTest::testBar",
  });
  assert.equal(record.provenance, EVIDENCE_PROVENANCE.CAPTURED);
  assert.equal(record.evidence_policy_version, EVIDENCE_POLICY_VERSION);
  assert.ok(record.text.includes("Failing tests: 1"));
  assert.ok(!record.text.includes("no gold method appears"));
  assert.equal(evidencePolicyCompliance(record).ok, true);
});

test("a manifest-recorded machine output is accepted when capture is unavailable", () => {
  const record = buildFailureEvidence({
    capturedText: "",
    manifestText: realDefects4jOutput(),
    failingTestIdentifier: "org.example.FooTest::testBar",
    captureError: "Defects4J is not available",
  });
  assert.equal(record.provenance, EVIDENCE_PROVENANCE.MANIFEST_RECORDED);
  assert.equal(record.capture_error, "Defects4J is not available");
  assert.equal(evidencePolicyCompliance(record).ok, true);
});

test("a manifest human summary is never shown to the agent and fails compliance", () => {
  const record = buildFailureEvidence({
    capturedText: "",
    manifestText: HUMAN_SUMMARY,
    failingTestIdentifier: "org.example.FooTest::testBar",
  });
  assert.equal(record.provenance, EVIDENCE_PROVENANCE.HUMAN_SUMMARY);
  assert.equal(record.text, "", "a human-authored summary must not reach the agent");
  const compliance = evidencePolicyCompliance(record);
  assert.equal(compliance.ok, false);
  assert.ok(compliance.reasons.some((reason) => reason.includes("human-authored summary")));
});

test("missing stack trace and missing raw output produce an explicit unavailable record", () => {
  const record = buildFailureEvidence({
    capturedText: "",
    manifestText: "",
    failingTestIdentifier: "org.example.FooTest::testBar",
  });
  assert.equal(record.provenance, EVIDENCE_PROVENANCE.UNAVAILABLE);
  assert.equal(record.text, "");
  const compliance = evidencePolicyCompliance(record);
  assert.equal(compliance.ok, false);
  assert.ok(compliance.reasons.some((reason) => reason.includes("No machine-generated failure evidence")));
});

test("a missing failing-test identifier fails compliance", () => {
  const record = buildFailureEvidence({
    capturedText: realDefects4jOutput(),
    failingTestIdentifier: "",
  });
  const compliance = evidencePolicyCompliance(record);
  assert.equal(compliance.ok, false);
  assert.ok(compliance.reasons.some((reason) => reason.includes("Failing test identifier")));
});

test("the failing-test identifier is carried verbatim into the record", () => {
  const testId = "com.google.javascript.jscomp.IntegrationTest::testConditionalPropertyCalls";
  const record = buildFailureEvidence({
    capturedText: realDefects4jOutput({ testId }),
    failingTestIdentifier: testId,
    allowedTestCommand: `defects4j test -t ${testId}`,
  });
  assert.equal(record.failing_test_identifier, testId);
  assert.equal(record.allowed_test_command, `defects4j test -t ${testId}`);
});

/* ------------------------------------------------------------ leakage control */

test("evidence naming private benchmark metadata is withheld from the agent", () => {
  const leaky = `${realDefects4jOutput()}\n    at Loader.load(gold_methods)`;
  const record = buildFailureEvidence({
    capturedText: leaky,
    failingTestIdentifier: "org.example.FooTest::testBar",
  });
  assert.equal(record.private_metadata_screen.ok, false);
  assert.deepEqual(record.private_metadata_screen.hits, ["gold_methods"]);
  assert.equal(record.text, "", "leaky evidence must not be exposed");
  assert.equal(evidencePolicyCompliance(record).ok, false);
});

test("a workspace path inside benchmark_runs is normalized away before screening", () => {
  const workspaceRoot = "/Users/x/defects4j/benchmark_runs/mini-swe-gpt56/CHART-1-L10-STRICT-001/run-001/workspace";
  const raw = `${realDefects4jOutput()}\nbuild dir: ${workspaceRoot}/Chart-1/build`;
  const record = buildFailureEvidence({
    capturedText: raw,
    failingTestIdentifier: "org.example.FooTest::testBar",
    workspaceRoot,
    repoRoot: "/Users/x/defects4j",
  });
  assert.equal(record.private_metadata_screen.ok, true);
  assert.ok(!record.text.includes("benchmark_runs"));
  assert.ok(record.text.includes("<WORKSPACE>"));
  assert.ok(record.text.length > 0);
});

test("the private metadata screen lists every infrastructure token it finds", () => {
  const screen = screenEvidenceForPrivateMetadata("reasoning_tree.yaml and variant.patch and ok");
  assert.equal(screen.ok, false);
  assert.deepEqual(screen.hits.sort(), ["reasoning_tree.yaml", "variant.patch"]);
});

/* ------------------------------------------------- cross-condition equivalence */

test("two conditions with equivalent failure output receive equivalent evidence formatting", () => {
  const shared = realDefects4jOutput({ testId: "org.example.FooTest::testBar" });
  const l10 = buildFailureEvidence({
    capturedText: shared,
    manifestText: HUMAN_SUMMARY,
    failingTestIdentifier: "org.example.FooTest::testBar",
    workspaceRoot: "/runs/l10/workspace",
    repoRoot: "/repo",
  });
  const l30 = buildFailureEvidence({
    capturedText: shared,
    manifestText: realDefects4jOutput({ testId: "org.example.FooTest::testBar" }),
    failingTestIdentifier: "org.example.FooTest::testBar",
    workspaceRoot: "/runs/l30/workspace",
    repoRoot: "/repo",
  });
  const comparison = evidenceFormattingEquivalent(l10, l30);
  assert.deepEqual(comparison.differences, []);
  assert.equal(comparison.equivalent, true);
  assert.equal(l10.text, l30.text, "identical underlying output must produce identical agent-visible text");
});

test("different depths are not given different evidence budgets", () => {
  const long = [
    "Failing tests: 1",
    "  - org.example.FooTest::testBar",
    ...Array.from({ length: 300 }, (_, index) => `    at org.example.Foo.m${index}(Foo.java:${index})`),
  ].join("\n");
  const depths = ["L10", "L30", "L50"].map((depth) =>
    buildFailureEvidence({
      capturedText: long,
      failingTestIdentifier: "org.example.FooTest::testBar",
      workspaceRoot: `/runs/${depth}/workspace`,
      repoRoot: "/repo",
    }),
  );
  const [first, ...rest] = depths;
  for (const record of rest) {
    assert.equal(record.text, first.text);
    assert.equal(record.truncated, first.truncated);
    assert.equal(record.line_count, first.line_count);
  }
  assert.equal(first.truncated, true, "the shared budget must actually bind on long output");
});

/* ------------------------------------------------------------------ versioning */

test("the policy version is frozen and recorded on every record", () => {
  assert.equal(EVIDENCE_POLICY_VERSION, "d4j-failure-evidence/v1");
  assert.equal(failureEvidencePolicy.policy_version, EVIDENCE_POLICY_VERSION);
  assert.equal(failureEvidencePolicy.identical_across_depths, true);
  assert.equal(failureEvidencePolicy.human_authored_summaries, "forbidden as a substitute for captured output");
  const record = buildFailureEvidence({ capturedText: realDefects4jOutput(), failingTestIdentifier: "a::b" });
  assert.equal(record.evidence_policy_version, EVIDENCE_POLICY_VERSION);
});

test("historical run manifests without the field are reported as legacy, never as compliant", () => {
  assert.equal(evidencePolicyVersionForManifest({ id: "old-run" }), LEGACY_EVIDENCE_POLICY_VERSION);
  assert.equal(evidencePolicyVersionForManifest(null), LEGACY_EVIDENCE_POLICY_VERSION);
  assert.equal(
    evidencePolicyVersionForManifest({ evidence: { evidence_policy_version: EVIDENCE_POLICY_VERSION } }),
    EVIDENCE_POLICY_VERSION,
  );
  const legacyCompliance = evidencePolicyCompliance({ evidence_policy_version: LEGACY_EVIDENCE_POLICY_VERSION, text: "x" });
  assert.equal(legacyCompliance.ok, false);
});

test("a mismatched policy version fails compliance", () => {
  const record = buildFailureEvidence({ capturedText: realDefects4jOutput(), failingTestIdentifier: "a::b" });
  const stale = { ...record, evidence_policy_version: "d4j-failure-evidence/v0" };
  const compliance = evidencePolicyCompliance(stale);
  assert.equal(compliance.ok, false);
  assert.ok(compliance.reasons.some((reason) => reason.includes("Evidence policy version")));
});
