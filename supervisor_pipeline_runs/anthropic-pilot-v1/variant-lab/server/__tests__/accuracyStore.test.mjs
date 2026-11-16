import assert from "node:assert/strict";
import test from "node:test";
import {
  aggregateCanonicalResults,
  buildAccuracyTaskRegistry,
  formatAccuracyCell,
  SEVEN_FAMILY_PILOT_FAMILIES,
  selectAccuracyMetric,
  summarizeAccuracyRecords,
} from "../accuracyStore.mjs";
import { evaluateRanking, parseTopTenRanking } from "../benchmarkStore.mjs";

function run(goldRank, { status = "completed", eligible = true } = {}) {
  return {
    gold_rank: goldRank,
    status,
    eligible,
    ranking_valid: status === "completed",
    included_in_accuracy: eligible && status === "completed",
    eligibility_reasons: eligible ? [] : ["excluded_fixture"],
  };
}

test("5/5 eligible rank-one runs aggregate to Accuracy@1 1.0", () => {
  const result = summarizeAccuracyRecords(Array.from({ length: 5 }, () => run(1)));
  assert.deepEqual(result.accuracy_at_1, { value: 1, numerator: 5, denominator: 5 });
});

test("4/5 eligible rank-one runs aggregate to Accuracy@1 0.8", () => {
  const result = summarizeAccuracyRecords([run(1), run(1), run(1), run(1), run(2)]);
  assert.deepEqual(result.accuracy_at_1, { value: 0.8, numerator: 4, denominator: 5 });
});

test("0/5 is a real zero when five eligible runs completed", () => {
  const result = summarizeAccuracyRecords(Array.from({ length: 5 }, () => run(2)));
  assert.deepEqual(result.accuracy_at_1, { value: 0, numerator: 0, denominator: 5 });
});

test("zero eligible completed runs produce null metrics", () => {
  const result = summarizeAccuracyRecords([]);
  assert.equal(result.accuracy_at_1.value, null);
  assert.equal(result.mean_reciprocal_rank.value, null);
  assert.equal(result.mean_gold_rank.value, null);
});

for (const status of ["failed", "timeout", "invalid_ranking"]) {
  test(`${status} run is excluded from accuracy`, () => {
    const result = summarizeAccuracyRecords([run(null, { status })]);
    assert.equal(result.n_attempted, 1);
    assert.equal(result.n_eligible, 0);
    assert.equal(result.accuracy_at_1.value, null);
  });
}

for (const availability of ["generation_failed", "validation_failed", "depth_unachievable"]) {
  test(`${availability} availability remains null`, () => {
    const result = summarizeAccuracyRecords([run(1)], { availability });
    assert.equal(result.n_eligible, 0);
    assert.equal(result.accuracy_at_1.value, null);
    assert.equal(formatAccuracyCell(result, "at1").display, "N/A");
  });
}

test("repeated runs use completed eligible runs as the denominator", () => {
  const result = summarizeAccuracyRecords([run(1), run(2), run(1), run(null, { status: "timeout" })], { targetRuns: 5 });
  assert.equal(result.n_attempted, 4);
  assert.equal(result.n_completed, 3);
  assert.equal(result.n_eligible, 3);
  assert.equal(result.accuracy_at_1.value, 2 / 3);
});

test("multiple gold methods use the first matching ranked prediction", () => {
  const evaluation = evaluateRanking(
    [{ rank: 1, class: "example.Other", method: "run" }, { rank: 2, class: "example.Foo", method: "fix" }],
    [{ class: "example.Foo", method: "fix" }, { class: "example.Bar", method: "fix" }],
  );
  assert.equal(evaluation.gold_rank, 2);
  assert.equal(evaluation.hit_at_5, true);
});

test("duplicate Top-10 predictions remain invalid", () => {
  const predictions = Array.from({ length: 10 }, (_, index) => ({ rank: index + 1, class: "example.Foo", method: index < 2 ? "same" : `m${index}` }));
  const parsed = parseTopTenRanking({ predictions });
  assert.equal(parsed.ok, false);
  assert.equal(parsed.errors.some((error) => error.includes("duplicate prediction")), true);
});

test("missing planned repetitions are progress, not failures", () => {
  const result = summarizeAccuracyRecords([run(1)], { targetRuns: 5 });
  assert.equal(result.target_runs, 5);
  assert.equal(result.n_eligible, 1);
  assert.deepEqual(result.accuracy_at_1, { value: 1, numerator: 1, denominator: 1 });
});

test("the seven-family pilot remains separate from the current nine-family cohort", () => {
  const manifest = {
    batch_id: "fixture",
    originals: [
      { project: "Chart", bug: 1, task_id: "Chart-1", status: "verified" },
      { project: "Gson", bug: 1, task_id: "Gson-1", status: "verified" },
    ],
    variants: [
      { project: "Chart", bug: 1, level: "L10", variant_id: "CHART-1-L10-FIXTURE", status: "validated" },
      { project: "Gson", bug: 1, level: "L10", variant_id: "GSON-1-L10-FIXTURE", status: "validated" },
    ],
  };
  const currentRegistry = buildAccuracyTaskRegistry([manifest]);
  const pilotRegistry = buildAccuracyTaskRegistry([manifest], SEVEN_FAMILY_PILOT_FAMILIES);
  const records = [
    { ...run(1), family: "Chart-1", depth: "L10" },
    { ...run(1), family: "Gson-1", depth: "L10" },
  ];
  const current = aggregateCanonicalResults(records, currentRegistry);
  const pilot = aggregateCanonicalResults(records, pilotRegistry, { families: SEVEN_FAMILY_PILOT_FAMILIES });
  assert.equal(current.depthSummary.find((row) => row.depth === "L10").n_eligible, 2);
  assert.equal(pilot.depthSummary.find((row) => row.depth === "L10").n_eligible, 1);
  assert.equal(pilot.familySummary.some((row) => row.family === "Gson-1"), false);
});

test("metric selection preserves canonical nulls instead of re-aggregating flattened cells", () => {
  const metric = { value: null, numerator: 0, denominator: 0, display: "N/A" };
  const analysis = {
    matrix: {
      rows: [{ family: "Chart-2", cells: { L10: { accuracy_at_1: null, metrics: { at1: metric, at5: metric, at10: metric, mrr: metric, mean_rank: metric } } } }],
    },
  };
  const selected = selectAccuracyMetric(analysis, "at1");
  assert.equal(selected.matrix.rows[0].cells.L10.selected.value, null);
});
