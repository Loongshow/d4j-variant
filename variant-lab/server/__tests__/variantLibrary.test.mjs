import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import {
  buildFaultLocalizationTask,
  chartSecondaryVariantId,
  artifactMapFor,
  createBatchReport,
  discoverVariantRecords,
  emptyFaultLocalizationResult,
  ensureChartSecondaryVariant,
  groupVariantRecords,
  hasCanonicalValidatedBugVariant,
  readVariantRecord,
  safeArtifactPath,
  sanitizeVariantId,
  summarizeVariantRecords,
  validationGatePasses,
  variantArtifactConsistency,
  variantBenchmarkEligibility,
} from "../variantLibrary.mjs";

async function withTempRepo(fn) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "d4j-variant-library-"));
  const variantsRoot = path.join(root, "new_bug_variants");
  const runsRoot = path.join(root, "runs");
  const checkoutRoot = path.join(root, "workspaces", "defects4j");
  await fs.mkdir(variantsRoot, { recursive: true });
  await fs.mkdir(runsRoot, { recursive: true });
  await fs.mkdir(checkoutRoot, { recursive: true });
  try {
    return await fn({ root, variantsRoot, runsRoot, checkoutRoot });
  } finally {
    await fs.rm(root, { recursive: true, force: true });
  }
}

async function writeJson(filePath, data) {
  await fs.writeFile(filePath, `${JSON.stringify(data, null, 2)}\n`);
}

async function writeFile(filePath, content) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, content);
}

test("migrates Chart secondary variant into canonical layout without failing the accepted gate", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot }) => {
    const migration = await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const records = await discoverVariantRecords(variantsRoot);

    assert.equal(records.length, 1);
    assert.equal(records[0].variantId, chartSecondaryVariantId);
    assert.equal(records[0].status, "validated");
    assert.equal(records[0].schema.ok, true);
    assert.equal(validationGatePasses(records[0].validation), true);
    assert.equal(variantBenchmarkEligibility(records[0]).ok, true);
    assert.match(await fs.readFile(path.join(migration.dir, "test.patch"), "utf8"), /LevelRenderer/);
    assert.match(migration.dir, /new_bug_variants\/Chart\/bug-1\/L10\/CHART-1-L10-SECONDARY-02$/);
  });
});

test("discovers canonical L50 variants", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot }) => {
    const migration = await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const l50Dir = path.join(variantsRoot, "Chart", "bug-1", "L50", "CHART-1-L50-001");
    await fs.mkdir(l50Dir, { recursive: true });
    for (const name of ["variant_manifest.json", "validation.json", "variant.patch", "test.patch", "reasoning_tree.yaml", "variant_report.md"]) {
      await fs.copyFile(path.join(migration.dir, name), path.join(l50Dir, name));
    }
    const manifestPath = path.join(l50Dir, "variant_manifest.json");
    const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
    manifest.variant_id = "CHART-1-L50-001";
    manifest.reasoning.level = "L50";
    await writeJson(manifestPath, manifest);

    const records = await discoverVariantRecords(variantsRoot);
    assert.equal(records.some((record) => record.variantId === "CHART-1-L50-001" && record.level === "L50"), true);
  });
});

test("historical validated status cannot override failed fresh reproduction", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot }) => {
    const migration = await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const manifestPath = path.join(migration.dir, "variant_manifest.json");
    const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
    manifest.status = "validated";
    manifest.benchmark_eligible = true;
    manifest.reproducibility = { status: "failed", reason: "fresh reconstruction did not fail" };
    await writeJson(manifestPath, manifest);

    const record = await readVariantRecord(migration.dir);
    const eligibility = variantBenchmarkEligibility(record);

    assert.equal(record.status, "needs_revalidation");
    assert.equal(eligibility.ok, false);
    assert.match(eligibility.reason, /fresh revalidation|requires fresh revalidation/i);
    assert.equal(hasCanonicalValidatedBugVariant([record], "Chart", "1", "L10"), false);
    assert.equal(variantBenchmarkEligibility(record, { debug_allow_unreproduced_variant: true }).ok, true);
  });
});

test("freshly reproduced variants are benchmark eligible only after reproducibility metadata is present", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot }) => {
    const migration = await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const record = await readVariantRecord(migration.dir);
    const eligibility = variantBenchmarkEligibility(record);

    assert.equal(record.status, "validated");
    assert.equal(eligibility.ok, true);
    assert.equal(eligibility.reproducibility_status, "passed");
    assert.equal(hasCanonicalValidatedBugVariant([record], "Chart", "1", "L10"), true);
  });
});

test("artifact consistency detects trigger renderer drift between manifest and test patch", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot }) => {
    const migration = await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const testPatchPath = path.join(migration.dir, "test.patch");
    const driftedPatch = (await fs.readFile(testPatchPath, "utf8")).replaceAll("LevelRenderer", "LineAndShapeRenderer");
    await fs.writeFile(testPatchPath, driftedPatch);
    const record = await readVariantRecord(migration.dir);
    const consistency = await variantArtifactConsistency(record);

    assert.equal(consistency.ok, false);
    assert.equal(consistency.checks.find((check) => check.id === "trigger:renderer-test-patch").status, "fail");
  });
});

test("artifact consistency detects a trigger renderer that bypasses the affected base method", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot, checkoutRoot }) => {
    const migration = await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const manifestPath = path.join(migration.dir, "variant_manifest.json");
    const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
    manifest.trigger.renderer = "org.jfree.chart.renderer.category.LineAndShapeRenderer";
    await writeJson(manifestPath, manifest);
    await writeFile(
      path.join(checkoutRoot, "Chart-1/fixed/source/org/jfree/chart/renderer/category/LineAndShapeRenderer.java"),
      `package org.jfree.chart.renderer.category;

public class LineAndShapeRenderer extends AbstractCategoryItemRenderer {
    public LegendItem getLegendItem(int datasetIndex, int series) {
        return null;
    }
}
`,
    );

    const record = await readVariantRecord(migration.dir);
    const consistency = await variantArtifactConsistency(record, { checkoutRoot });

    assert.equal(consistency.ok, false);
    assert.equal(consistency.checks.find((check) => check.id === "call-path:renderer-does-not-override-fault-method").status, "fail");
  });
});

test("artifact consistency accepts plot-owned fault evidence without renderer inheritance checks", async () => {
  await withTempRepo(async ({ variantsRoot }) => {
    const variantId = "CHART-1-L20-001";
    const variantDir = path.join(variantsRoot, "Chart", "bug-1", "L20", variantId);
    const trigger =
      "org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests::testLegendItemsUseRendererIndexMapping";
    const manifest = {
      schema_version: "d4j-variant-manifest/v1",
      variant_id: variantId,
      source: {
        defects4j_project: "Chart",
        defects4j_bug_id: 1,
        fixed_revision: "2266",
        artifact_path: `new_bug_variants/Chart/bug-1/L20/${variantId}/`,
      },
      status: "validated",
      benchmark_eligible: true,
      reproducibility: { status: "passed" },
      reasoning: {
        level: "L20",
        unit_count: 18,
        changed_node: "D: renderer-to-plot index mapping resolves the dataset index",
      },
      fault: {
        locations: [
          {
            class: "org.jfree.chart.plot.CategoryPlot",
            method: "getIndexOf",
            file: "source/org/jfree/chart/plot/CategoryPlot.java",
            line_hint: "return this.renderers.indexOf(renderer);",
            production: true,
          },
        ],
        gold: {
          faulty_class: "org.jfree.chart.plot.CategoryPlot",
          faulty_method: "getIndexOf",
        },
      },
      trigger: {
        test_id: trigger,
        test_method: "testLegendItemsUseRendererIndexMapping",
        renderer: "org.jfree.chart.renderer.category.LineAndShapeRenderer",
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
        variant_trigger_runs: [
          { status: "expected_fail" },
          { status: "expected_fail" },
          { status: "expected_fail" },
        ],
        deterministic: { status: "pass" },
        production_fault: { status: "pass" },
        gold_method_known: { status: "pass" },
      },
    };

    await fs.mkdir(variantDir, { recursive: true });
    await writeJson(path.join(variantDir, "variant_manifest.json"), manifest);
    await writeJson(path.join(variantDir, "validation.json"), validation);
    await writeFile(
      path.join(variantDir, "variant.patch"),
      "public int getIndexOf(CategoryItemRenderer renderer) {\n-        return this.renderers.indexOf(renderer);\n+        int result = this.renderers.indexOf(renderer);\n",
    );
    await writeFile(
      path.join(variantDir, "test.patch"),
      "public void testLegendItemsUseRendererIndexMapping() {\n    CategoryPlot plot = new CategoryPlot();\n    new LineAndShapeRenderer();\n}\n",
    );
    await writeFile(
      path.join(variantDir, "variant_report.md"),
      "CategoryPlot::getIndexOf is exercised by testLegendItemsUseRendererIndexMapping using LineAndShapeRenderer.\n",
    );
    await writeFile(path.join(variantDir, "reasoning_tree.yaml"), "variant_id: CHART-1-L20-001\n");
    await writeFile(
      path.join(variantDir, "validation.log"),
      `${trigger}\nrun 1: ComparisonFailure expected Secondary observed Primary\n`,
    );
    await writeFile(path.join(variantDir, "generation_trace.json"), "{}\n");

    const record = await readVariantRecord(variantDir);
    const consistency = await variantArtifactConsistency(record);

    assert.equal(consistency.ok, true);
    assert.equal(consistency.checks.find((check) => check.id === "fault:test-patch-owner").status, "pass");
    assert.equal(consistency.checks.find((check) => check.id === "fault:report-owner").status, "pass");
    assert.equal(
      consistency.checks.some((check) => check.id.startsWith("call-path:renderer-")),
      false,
    );
  });
});

test("artifact consistency checks manifest patch hashes", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot }) => {
    const migration = await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const manifestPath = path.join(migration.dir, "variant_manifest.json");
    const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
    manifest.reproducibility.artifact_hashes = {
      test_patch: "deadbeef",
    };
    await writeJson(manifestPath, manifest);
    const record = await readVariantRecord(migration.dir);
    const consistency = await variantArtifactConsistency(record);

    assert.equal(consistency.ok, false);
    assert.equal(consistency.checks.find((check) => check.id === "hash:test_patch").status, "fail");
  });
});

test("groups variant records by project, bug, and level", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot }) => {
    await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const records = await discoverVariantRecords(variantsRoot);
    const groups = groupVariantRecords(records);
    const summary = summarizeVariantRecords(records);

    assert.equal(groups[0].project, "Chart");
    assert.equal(groups[0].bugs[0].bugId, 1);
    assert.equal(groups[0].bugs[0].levels[0].level, "L10");
    assert.equal(groups[0].bugs[0].levels[0].variants[0].variant_id, chartSecondaryVariantId);
    assert.deepEqual(summary.levels, { L10: 1, L20: 0, L30: 0, L50: 0, L70: 0, L90: 0 });
    assert.equal(summary.validated, 1);
  });
});

test("rejects unsafe variant ids and artifact paths", async () => {
  assert.equal(sanitizeVariantId("CHART-1-L10-SECONDARY-02"), "CHART-1-L10-SECONDARY-02");
  assert.throws(() => sanitizeVariantId("../secret"), /Invalid variant id/);
  assert.throws(() => sanitizeVariantId("/tmp/secret"), /Invalid variant id/);

  const root = await fs.mkdtemp(path.join(os.tmpdir(), "d4j-safe-path-"));
  try {
    assert.equal(path.basename(safeArtifactPath(root, "variant.patch")), "variant.patch");
    assert.throws(() => safeArtifactPath(root, "../variant.patch"), /Invalid artifact name|Rejected path traversal/);
  } finally {
    await fs.rm(root, { recursive: true, force: true });
  }
});

test("batch helper can skip an existing validated Chart variant", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot }) => {
    await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const records = await discoverVariantRecords(variantsRoot);

    assert.equal(hasCanonicalValidatedBugVariant(records, "Chart", "1", "L10"), true);
    assert.equal(hasCanonicalValidatedBugVariant(records, "Cli", "1", "L10"), false);
  });
});

test("batch report persists every attempted project result", async () => {
  await withTempRepo(async ({ root, runsRoot }) => {
    const batch = await createBatchReport({
      repoRoot: root,
      runsRoot,
      projects: ["Chart", "Cli"],
      results: [
        {
          project: "Chart",
          bug: 1,
          variant_id: chartSecondaryVariantId,
          status: "skipped_existing_validated",
          reason: "Validated canonical L10 variant already exists",
        },
        {
          project: "Cli",
          bug: 1,
          variant_id: "CLI-1-L10-RUN-001",
          status: "generation_failed",
          reason: "No accepted candidate",
        },
      ],
    });

    assert.equal(batch.results.length, 2);
    assert.match(await fs.readFile(path.join(root, batch.report_path), "utf8"), /Cli/);
  });
});

test("fault-localization task exposes only the strict benchmark whitelist", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot, checkoutRoot }) => {
    await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const [record] = await discoverVariantRecords(variantsRoot);
    const task = buildFaultLocalizationTask({ record, checkoutRoot });
    const text = JSON.stringify(task);

    assert.deepEqual(Object.keys(task).sort(), [
      "failing_test_identifier",
      "failing_test_source",
      "read_only_buggy_repository_path",
      "stack_trace",
      "task_id",
      "variant_id",
    ]);
    assert.doesNotMatch(text, /reasoning_tree|variant\.patch|test\.patch|gold|variant_report|fixed source/i);
    assert.match(task.failing_test_identifier, /testLegendItemsForSecondaryDataset/);
  });
});

test("fault-localization result can represent provider-not-configured without fake predictions", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot }) => {
    await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const [record] = await discoverVariantRecords(variantsRoot);
    const result = emptyFaultLocalizationResult({ record, runId: "fl-test", status: "provider_not_configured" });

    assert.equal(result.status, "provider_not_configured");
    assert.deepEqual(result.predictions, []);
    assert.equal(result.gold_rank, null);
  });
});
