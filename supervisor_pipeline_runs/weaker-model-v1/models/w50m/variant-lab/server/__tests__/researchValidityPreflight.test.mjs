import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { runResearchValidityPreflight } from "../researchValidityPreflight.mjs";
import {
  STRICT_EXPERIMENT_COHORT_ID,
  STRICT_EXPERIMENT_CONDITIONS,
  STRICT_EXPERIMENT_ID,
  SUPERSEDED_EXPERIMENT_IDS,
  STRICT_EXPERIMENT_BUDGET,
} from "../strictExperiment.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

// The full-condition preflight walks the repository, so it is computed once and shared.
let fullReportPromise = null;
function fullReport() {
  fullReportPromise ??= runResearchValidityPreflight({
    repoRoot,
    cohortId: STRICT_EXPERIMENT_COHORT_ID,
    conditions: STRICT_EXPERIMENT_CONDITIONS,
    experimentId: STRICT_EXPERIMENT_ID,
  });
  return fullReportPromise;
}

test("the strict experiment uses a new id and never reuses the historical stop record", () => {
  assert.equal(STRICT_EXPERIMENT_ID, "strict-chart-closure-l10-l30-v1");
  assert.ok(SUPERSEDED_EXPERIMENT_IDS.includes("chart-closure-l10-l30-pilot"));
  assert.ok(!SUPERSEDED_EXPERIMENT_IDS.includes(STRICT_EXPERIMENT_ID));
});

test("the frozen budget matches the protocol", () => {
  assert.deepEqual(STRICT_EXPERIMENT_BUDGET, {
    max_tool_calls: 50,
    max_test_runs: 5,
    timeout_seconds: 300,
    agent_startup_timeout_seconds: 30,
    repeats: 1,
  });
});

test("the six conditions are declared in a fixed order with shortcut risk recorded", () => {
  assert.equal(STRICT_EXPERIMENT_CONDITIONS.length, 6);
  assert.deepEqual(
    STRICT_EXPERIMENT_CONDITIONS.map((condition) => condition.order),
    [1, 2, 3, 4, 5, 6],
  );
  for (const condition of STRICT_EXPERIMENT_CONDITIONS) {
    assert.ok(condition.shortcut_risk, `${condition.arm} must declare shortcut_risk`);
  }
  const chartL30 = STRICT_EXPERIMENT_CONDITIONS.find((condition) => condition.arm === "Chart-1 strict L30");
  assert.equal(chartL30.shortcut_risk, "high");
  const closureL30 = STRICT_EXPERIMENT_CONDITIONS.find((condition) => condition.arm === "Closure-1 strict L30");
  assert.equal(closureL30.shortcut_risk, "low");
});

test("the disqualified Closure L10 artifact is never substituted into the L10 arm", () => {
  const arm = STRICT_EXPERIMENT_CONDITIONS.find((condition) => condition.arm === "Closure-1 strict L10");
  assert.equal(arm.variant_id, "CLOSURE-1-L10-STRICT-001");
  assert.notEqual(arm.variant_id, "CLOSURE-1-L10-001");
});

test("the preflight launches nothing and reports a decision", async (t) => {
  const report = await fullReport();
  if (!report.global_checks.find((item) => item.id === "historical:variants-discoverable")?.message?.includes("47")) {
    t.diagnostic("running outside the full repository; structural assertions only");
  }

  assert.equal(report.agent_processes_launched, 0);
  assert.equal(report.benchmark_runs_created, 0);
  assert.equal(report.launch_authorized, false);
  assert.equal(report.cohort_id, STRICT_EXPERIMENT_COHORT_ID);
  assert.equal(report.conditions.length, 6);
  assert.ok(["STOP_BEFORE_AGENT_LAUNCH", "ALL_CONDITIONS_READY_AWAITING_USER_AUTHORIZATION"].includes(report.decision));
});

test("a missing artifact makes its condition NOT READY and the whole experiment NOT READY", async () => {
  // Exercises the MECHANISM with a deliberately absent id, so the test does not encode
  // the repository's transient state. (Closure-1 strict L10 was missing until
  // CLOSURE-1-L10-STRICT-001 was constructed and validated on 2026-09-14.)
  const report = await runResearchValidityPreflight({
    repoRoot,
    cohortId: STRICT_EXPERIMENT_COHORT_ID,
    conditions: [
      ...STRICT_EXPERIMENT_CONDITIONS,
      { arm: "Deliberately absent arm", order: 7, task_type: "variant", variant_id: "NOSUCH-1-L10-001", required_level: "L10" },
    ],
    experimentId: "gate-check-missing-artifact",
  });
  const absent = report.conditions.find((condition) => condition.arm === "Deliberately absent arm");
  assert.equal(absent.ready, false);
  assert.equal(absent.checks.find((item) => item.id === "condition:artifact-exists").status, "fail");
  assert.equal(report.experiment_ready, false);
  assert.equal(report.decision, "STOP_BEFORE_AGENT_LAUNCH");
  assert.ok(report.not_ready_conditions.includes("Deliberately absent arm"));
});

test("the strict Closure L10 arm now resolves to a validated, depth-audited artifact", async () => {
  const report = await fullReport();
  const arm = report.conditions.find((condition) => condition.arm === "Closure-1 strict L10");
  assert.equal(arm.checks.find((item) => item.id === "condition:artifact-exists").status, "pass");
  const depth = arm.checks.find((item) => item.id === "condition:audited-depth");
  assert.equal(depth.status, "pass");
  assert.ok(depth.audited_semantic_depth >= 10, `audited depth ${depth.audited_semantic_depth} must meet the strict L10 bound`);
  assert.notEqual(depth.audited_semantic_depth, null);
});

test("a cohort that does not support strict claims fails the gate", async () => {
  const report = await runResearchValidityPreflight({
    repoRoot,
    cohortId: "seven-family-l10-l90-v1",
    conditions: [],
    experimentId: "gate-check",
  });
  const cohortCheck = report.global_checks.find((item) => item.id === "cohort:explicit");
  assert.equal(cohortCheck.status, "fail");
  assert.equal(report.experiment_ready, false);
});

test("an unknown cohort id fails the gate rather than defaulting", async () => {
  const report = await runResearchValidityPreflight({
    repoRoot,
    cohortId: "not-a-real-cohort",
    conditions: [],
    experimentId: "gate-check",
  });
  const cohortCheck = report.global_checks.find((item) => item.id === "cohort:explicit");
  assert.equal(cohortCheck.status, "fail");
  assert.match(cohortCheck.message, /Unknown cohort id/);
});

test("the frozen prompt and evidence policy are verified by the gate", async () => {
  const report = await runResearchValidityPreflight({
    repoRoot,
    cohortId: STRICT_EXPERIMENT_COHORT_ID,
    conditions: [],
    experimentId: "gate-check",
  });
  assert.equal(report.global_checks.find((item) => item.id === "protocol:prompt-frozen").status, "pass");
  assert.equal(report.global_checks.find((item) => item.id === "protocol:evidence-policy-frozen").status, "pass");
});

test("an unverified check never counts as a pass", async () => {
  const report = await fullReport();
  for (const condition of report.conditions) {
    const hasBlocking = condition.checks.some((item) => item.status === "fail" || item.status === "unverified");
    assert.equal(condition.ready, !hasBlocking, `${condition.arm} readiness must exclude fail and unverified`);
  }
});
