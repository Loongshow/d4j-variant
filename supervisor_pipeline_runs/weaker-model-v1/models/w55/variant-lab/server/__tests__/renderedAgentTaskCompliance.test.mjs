/**
 * Regression tests for the rendered-agent-task compliance gate.
 *
 * These cover the failure that halted strict-depth-chart-closure-v1 at condition 2:
 * CHART-1-L10-STRICT-001 passed every package-metadata check, was reported READY by the
 * research-validity preflight, and was then refused in 0.3 s by the run-time isolation
 * guard because its agent-visible task carried a human-authored summary containing the
 * token "gold".
 *
 * The gate inspects the FINAL rendered payload, not package metadata.
 */
import assert from "node:assert/strict";
import test from "node:test";

import { renderedAgentTaskCompliance } from "../researchValidityPreflight.mjs";
import { assertAgentTaskIsolation } from "../benchmarkStore.mjs";

const MACHINE_GENERATED_TRACE = [
  "Running ant (compile.tests).... OK",
  "Running ant (run.dev.tests).... OK",
  "Failing tests: 1",
  "  - org.jfree.chart.plot.junit.CategoryPlotTests::testGeneratedItemMetadata",
].join("\n");

const REAL_TEST_SOURCE = [
  "    public void testGeneratedItemMetadata() {",
  "        DefaultCategoryDataset d0 = new DefaultCategoryDataset();",
  '        d0.addValue(1.0, "R7", "C4");',
  '        assertEquals("1:R2:R2:true:2:R2:true", observed);',
  "    }",
].join("\n");

function task(overrides = {}) {
  return {
    schema_version: "d4j-agent-visible-task/v1",
    task_id: "CHART-1-L10-STRICT-001",
    failing_test_identifier: "org.jfree.chart.plot.junit.CategoryPlotTests::testGeneratedItemMetadata",
    failing_test_source: REAL_TEST_SOURCE,
    stack_trace: MACHINE_GENERATED_TRACE,
    read_only_buggy_repository_path: "/workspaces/defects4j/Chart-1/variant",
    allowed_test_command:
      "defects4j test -t org.jfree.chart.plot.junit.CategoryPlotTests::testGeneratedItemMetadata",
    source_immutability: {
      production_and_test_source: "immutable",
      build_and_temp_outputs: "writable",
    },
    ...overrides,
  };
}

// A. The exact prose that halted the experiment must be rejected.
test("A: human-authored 'no gold method appears' evidence is rejected", () => {
  const result = renderedAgentTaskCompliance(
    task({
      stack_trace:
        "ComparisonFailure in CategoryPlotTests.testGeneratedItemMetadata; no gold method appears.",
    }),
  );

  assert.equal(result.ok, false);
  assert.equal(result.stack_trace_classification, "human_authored_summary");
  assert.ok(
    result.reasons.some((reason) => reason.includes("human-authored")),
    `expected a human-authored rejection reason, got ${JSON.stringify(result.reasons)}`,
  );
  // It must also be caught by the isolation guard, exactly as it was at launch.
  assert.equal(result.isolation_ok, false);
});

test("A2: a human-authored summary with no banned token is still rejected as non-captured", () => {
  const result = renderedAgentTaskCompliance(
    task({ stack_trace: "The renderer returns the wrong legend label for the second dataset." }),
  );

  assert.equal(result.ok, false);
  assert.equal(result.isolation_ok, true, "no banned token, so the isolation guard alone would allow it");
  assert.equal(result.stack_trace_classification, "human_authored_summary");
});

// B. An empty failing_test_source is rejected.
test("B: empty failing_test_source is rejected", () => {
  const result = renderedAgentTaskCompliance(task({ failing_test_source: "" }));

  assert.equal(result.ok, false);
  assert.equal(result.failing_test_source_chars, 0);
  assert.ok(result.reasons.some((reason) => reason.includes("failing_test_source is empty")));
});

test("B2: empty stack_trace is rejected", () => {
  const result = renderedAgentTaskCompliance(task({ stack_trace: "" }));

  assert.equal(result.ok, false);
  assert.ok(result.reasons.some((reason) => reason.includes("stack_trace is empty")));
});

// C. Valid machine-generated evidence passes.
test("C: valid machine-generated failure evidence passes", () => {
  const result = renderedAgentTaskCompliance(task());

  assert.equal(result.ok, true, `unexpected reasons: ${JSON.stringify(result.reasons)}`);
  assert.equal(result.reasons.length, 0);
  assert.equal(result.stack_trace_classification, "machine_generated");
  assert.equal(result.isolation_ok, true);
  assert.ok(result.failing_test_source_chars > 0);
  assert.deepEqual(result.private_metadata_hits, []);
});

test("C2: a real JUnit stack frame also counts as captured output", () => {
  const result = renderedAgentTaskCompliance(
    task({
      stack_trace: [
        "java.lang.IllegalStateException: set methods must have exactly one parameter",
        "    at com.google.javascript.jscomp.Compiler.compile(Compiler.java:632)",
      ].join("\n"),
    }),
  );

  assert.equal(result.ok, true, `unexpected reasons: ${JSON.stringify(result.reasons)}`);
  assert.equal(result.stack_trace_classification, "machine_generated");
});

// D. Benchmark / gold metadata leakage is rejected.
test("D: gold and benchmark metadata leakage is rejected", () => {
  for (const leak of [
    "Failing tests: 1\n  - the gold method is AbstractCategoryItemRenderer#getLegendItems",
    "Failing tests: 1\n  - see new_bug_variants/Chart/bug-1/L10/variant_manifest.json",
    "Failing tests: 1\n  - reasoning_tree.yaml records the dependency",
  ]) {
    const result = renderedAgentTaskCompliance(task({ stack_trace: leak }));
    assert.equal(result.ok, false, `leak was not rejected: ${leak}`);
  }
});

test("D2: leakage in failing_test_source is rejected, not only in the stack trace", () => {
  const result = renderedAgentTaskCompliance(
    task({ failing_test_source: `${REAL_TEST_SOURCE}\n// see validation.log for the gold method` }),
  );

  assert.equal(result.ok, false);
});

// E. The gate is read-only: it must not mutate the task it inspects.
test("E: the compliance gate does not mutate the rendered task", () => {
  const subject = task();
  const before = JSON.stringify(subject);

  renderedAgentTaskCompliance(subject);

  assert.equal(JSON.stringify(subject), before, "renderedAgentTaskCompliance mutated its input");
});

test("E2: the gate agrees with the run-time isolation guard on the same payload", () => {
  // The preflight must never report READY for a payload the run-time guard will refuse.
  const leaking = task({ stack_trace: "ComparisonFailure; no gold method appears." });
  const runtime = assertAgentTaskIsolation(leaking);
  const preflight = renderedAgentTaskCompliance(leaking);

  assert.equal(runtime.ok, false);
  assert.equal(preflight.ok, false);
  assert.equal(preflight.isolation_ok, runtime.ok);
});
