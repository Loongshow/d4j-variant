import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import {
  DEFAULT_BATCH_ID,
  DEPTH_LADDER_BATCH_ID,
  accuracyAtOneMatrix,
  checkpointBatchEntry,
  createBatchManifest,
  ensureBatch,
  isTerminalBatchEntry,
  nextBatchEntry,
  rowsToCsv,
  variantMatrixRows,
  writeBatchOutputs,
} from "../batchStore.mjs";
import {
  buildReasoningWorkflow,
  validateAgentEvidenceChain,
  validateReasoningWorkflow,
} from "../reasoningWorkflow.mjs";
import { buildJavaMethodCatalogEntries } from "../agents/agentAdapter.mjs";

async function withTempBenchmark(fn) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "d4j-batch-store-"));
  const benchmarkRoot = path.join(root, "benchmark_runs");
  try {
    await fs.mkdir(benchmarkRoot, { recursive: true });
    await fn({ root, benchmarkRoot });
  } finally {
    await fs.rm(root, { recursive: true, force: true });
  }
}

test("batch initializes all nine originals and twenty-seven ordered variants", () => {
  const manifest = createBatchManifest(DEFAULT_BATCH_ID, "2026-09-03T00:00:00.000Z");
  assert.equal(manifest.originals.length, 9);
  assert.equal(manifest.variants.length, 27);
  assert.deepEqual(
    manifest.variants.slice(0, 3).map((entry) => entry.key),
    ["Cli-1:L10", "Cli-1:L30", "Cli-1:L50"],
  );
  assert.equal(nextBatchEntry(manifest).key, "Cli-1:Original");
});

test("depth-ladder batch initializes seven evidence-selected families and five levels", () => {
  const manifest = createBatchManifest(DEPTH_LADDER_BATCH_ID, "2026-09-08T00:00:00.000Z");
  assert.equal(manifest.originals.length, 7);
  assert.equal(manifest.variants.length, 35);
  assert.deepEqual(manifest.level_order, ["L10", "L30", "L50", "L70", "L90"]);
  assert.deepEqual(manifest.project_order, ["Chart", "Math", "Codec", "Closure", "Cli", "Collections", "Csv"]);
});

test("Accuracy@1 matrix excludes failed runs and reports N/A", () => {
  const manifest = createBatchManifest(DEPTH_LADDER_BATCH_ID, "2026-09-08T00:00:00.000Z");
  const chartL10 = manifest.variants.find((entry) => entry.key === "Chart-1:L10");
  chartL10.status = "validated";
  chartL10.benchmark_eligible = true;
  chartL10.benchmark_status = "completed";
  chartL10.metrics = { gold_rank: 1 };
  const chartL30 = manifest.variants.find((entry) => entry.key === "Chart-1:L30");
  chartL30.status = "validated";
  chartL30.benchmark_status = "timeout";
  chartL30.metrics = { gold_rank: null };

  const matrix = accuracyAtOneMatrix(manifest);
  const chart = matrix.rows.find((row) => row.project === "Chart");
  assert.equal(chart.cells.L10.display, "1.00 (1/1)");
  assert.equal(chart.cells.L30.display, "N/A");
  assert.equal(chart.cells.L30.denominator, 0);
});

test("batch checkpoint resumes without replacing completed fields", async () => {
  await withTempBenchmark(async ({ benchmarkRoot }) => {
    await ensureBatch(benchmarkRoot);
    await checkpointBatchEntry(benchmarkRoot, DEFAULT_BATCH_ID, "Cli-1:Original", {
      status: "verified",
      current_stage: "benchmark_original",
      resume_from: "benchmark_original",
      artifact_paths: ["first.json"],
    });
    const updated = await checkpointBatchEntry(benchmarkRoot, DEFAULT_BATCH_ID, "Cli-1:Original", {
      benchmark_status: "completed",
      benchmark_run_id: "run-001",
      artifact_paths: ["second.json"],
    });
    assert.deepEqual(updated.entry.artifact_paths, ["first.json", "second.json"]);
    assert.equal(updated.entry.status, "verified");
    assert.equal(isTerminalBatchEntry(updated.entry), true);
    assert.equal(nextBatchEntry(updated.manifest).key, "Cli-1:L10");
  });
});

test("terminal generation failure continues to the next level", () => {
  const manifest = createBatchManifest(DEFAULT_BATCH_ID, "2026-09-03T00:00:00.000Z");
  manifest.originals[0].status = "verified";
  manifest.originals[0].benchmark_status = "completed";
  manifest.variants[0].status = "generation_failed";
  assert.equal(nextBatchEntry(manifest).key, "Cli-1:L30");
});

test("dependency-skipped L50 is terminal and does not block later projects", () => {
  const manifest = createBatchManifest(DEFAULT_BATCH_ID, "2026-09-03T00:00:00.000Z");
  manifest.originals[0].status = "verified";
  manifest.originals[0].benchmark_status = "completed";
  manifest.variants[0].status = "generation_failed";
  manifest.variants[1].status = "generation_failed";
  manifest.variants[2].status = "not_attempted_due_to_dependency";
  assert.equal(isTerminalBatchEntry(manifest.variants[2]), true);
  assert.equal(nextBatchEntry(manifest).key, "Collections-1:Original");
});

test("depth unachievable remains explicit and metrics are blank rather than fake zeroes", () => {
  const manifest = createBatchManifest(DEFAULT_BATCH_ID, "2026-09-03T00:00:00.000Z");
  manifest.variants[2].status = "depth_unachievable";
  const row = variantMatrixRows(manifest)[2];
  assert.equal(row["Generation Status"], "depth_unachievable");
  assert.equal(row["Gold Rank"], null);
  assert.match(rowsToCsv([row]), /depth_unachievable/);
  assert.doesNotMatch(rowsToCsv([row]), /,0,/);
});

test("batch outputs are durable and include aggregate files", async () => {
  await withTempBenchmark(async ({ benchmarkRoot }) => {
    await ensureBatch(benchmarkRoot);
    const output = await writeBatchOutputs(benchmarkRoot);
    for (const name of [
      "batch_manifest.json",
      "variant_matrix.csv",
      "benchmark_results.csv",
      "acc1_matrix.csv",
      "acc1_matrix.json",
      "original_vs_variant_summary.json",
      "depth_summary.json",
      "reasoning_workflow_summary.json",
      "shortcut_audit.csv",
      "workflow_summary.json",
      "REPORT.md",
    ]) {
      await fs.access(path.join(output.dir, name));
    }
    assert.equal(output.comparison.interpretation_guard.includes("definitive proof"), true);
    assert.equal(output.manifest.research_framing.same_model_family, true);
    assert.equal(output.fileOverlapMatrices.length, 9);
    assert.deepEqual(output.comparison.families[0].private_variants[0].file_overlap, output.fileOverlapMatrices[0].pairs[0]);
    await fs.access(path.join(output.dir, "file_overlap_matrices", "Cli-1.json"));
  });
});

test("reasoning workflow preserves source labels and objective event order", () => {
  const workflow = buildReasoningWorkflow({
    runId: "run-001",
    trajectory: [
      { sequence: 1, timestamp: "2026-09-03T00:00:01Z", type: "test_run", target: "defects4j test" },
      { sequence: 2, timestamp: "2026-09-03T00:00:02Z", type: "search", target: "rg failure" },
      { sequence: 3, timestamp: "2026-09-03T00:00:03Z", type: "open_file", target: "src/main/Foo.java" },
    ],
    structuredSubmission: {
      ok: true,
      prediction_count: 10,
      submitted_at: "2026-09-03T00:00:04Z",
      predictions: [{ class: "example.Foo", method: "bar" }],
      evidence_chain: [
        {
          evidence: "The failing path reads Foo.java.",
          inference_summary: "Foo::bar remains a candidate.",
          candidate_methods: ["example.Foo::bar"],
        },
      ],
    },
  });
  assert.equal(validateReasoningWorkflow(workflow).ok, true);
  assert.deepEqual(new Set(workflow.nodes.map((node) => node.source_type)), new Set(["observed", "agent_reported"]));
  assert.equal(workflow.nodes.some((node) => node.kind === "final_submission"), true);
  assert.equal(workflow.nodes.some((node) => node.source_type === "derived"), false);
});

test("malformed optional evidence chain never invalidates the ranking transport", () => {
  const validation = validateAgentEvidenceChain("not-an-array");
  assert.equal(validation.ok, false);
  const workflow = buildReasoningWorkflow({
    runId: "run-002",
    trajectory: [],
    structuredSubmission: { ok: true, prediction_count: 10, predictions: [], evidence_chain: "bad" },
  });
  assert.equal(workflow.agent_reported_chain_status, "rejected");
  assert.equal(workflow.nodes.some((node) => node.kind === "final_submission"), true);
});

test("JDK production catalog recognizes constructors and nested-class methods", async () => {
  await withTempBenchmark(async ({ root }) => {
    const file = path.join(root, "src/main/java/example/Outer.java");
    await fs.mkdir(path.dirname(file), { recursive: true });
    await fs.writeFile(
      file,
      `package example;
public class Outer {
  public Outer() {}
  static class Inner {
    int update(int value) { return value; }
  }
}
`,
    );
    const catalog = await buildJavaMethodCatalogEntries(root);
    assert.equal(catalog.some((entry) => entry.qualified === "example.Outer::Outer"), true);
    assert.equal(catalog.some((entry) => entry.qualified === "example.Outer$Inner::update"), true);
  });
});
