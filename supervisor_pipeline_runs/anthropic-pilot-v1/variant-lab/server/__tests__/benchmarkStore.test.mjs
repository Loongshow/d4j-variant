import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { promisify } from "node:util";
import {
  LOCALIZATION_SYSTEM_PROMPT,
  buildJavaMethodCatalogEntries,
  compareSourceHashes,
  hashSourceFiles,
  normalizeTrajectoryEvents,
  renderLocalizationPrompt,
  scanPrivateMetadata,
} from "../agents/agentAdapter.mjs";
import {
  MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS,
  MiniSweAgentAdapter,
  miniSweRuntimeModelName,
} from "../agents/miniSweAgentAdapter.mjs";
import { resolveProviderConfig } from "../agents/providerConfig.mjs";
import { hasRequiredEvidence, normalizeJavaMethodIdentity } from "../variantConstruction.mjs";
import {
  assertAgentTaskIsolation,
  assertNoCredentialFields,
  buildChartDepthLadder,
  buildOriginalAgentTask,
  buildVariantAgentTask,
  compareOriginalVariantRuns,
  computeBehaviorMetrics,
  createBenchmarkRun,
  defaultAgentProfiles,
  discoverBenchmarkRunRecords,
  evaluateRanking,
  fileOverlap,
  findBenchmarkRunById,
  listAgentProfiles,
  parseTopTenRanking,
  parseBenchmarkDurationMs,
  readBenchmarkArtifact,
  sanitizeBenchmarkId,
  saveAgentProfile,
  withAgentRuntimeStatus,
} from "../benchmarkStore.mjs";
import { ensureChartSecondaryVariant } from "../variantLibrary.mjs";

const execFileAsync = promisify(execFile);

async function withTempRepo(fn) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "d4j-benchmark-store-"));
  const benchmarkRoot = path.join(root, "benchmark_runs");
  const variantsRoot = path.join(root, "new_bug_variants");
  const runsRoot = path.join(root, "runs");
  const checkoutRoot = path.join(root, "workspaces", "defects4j");
  await fs.mkdir(benchmarkRoot, { recursive: true });
  await fs.mkdir(variantsRoot, { recursive: true });
  await fs.mkdir(runsRoot, { recursive: true });
  await fs.mkdir(checkoutRoot, { recursive: true });
  try {
    return await fn({ root, benchmarkRoot, variantsRoot, runsRoot, checkoutRoot });
  } finally {
    await fs.rm(root, { recursive: true, force: true });
  }
}

async function writeFile(filePath, content) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, content);
}

async function writeFakeChartCheckout(checkoutRoot, version = "buggy", options = {}) {
  const checkout = path.join(checkoutRoot, "Chart-1", version);
  await writeFile(
    path.join(checkout, "source/org/example/Prod.java"),
    `package org.example;

public class Prod {
    public int m0() { return 0; }
    public int m1() { return 1; }
    public int m2() { return 2; }
    public int m3() { return 3; }
    public int m4() { return 4; }
    public int m5() { return 5; }
    public int m6() { return 6; }
    public int m7() { return 7; }
    public int m8() { return 8; }
    public int m9() { return 9; }
}
`,
  );
  await writeFile(
    path.join(checkout, "tests/org/example/ProdTest.java"),
    `package org.example;

public class ProdTest {
    public void testBug() {}
}
`,
  );
  await writeFile(path.join(checkout, ".git/config"), "[core]\nrepositoryformatversion = 0\n");
  await writeFile(path.join(checkout, ".svn/entries"), "metadata\n");
  if (options.privateFiles) {
    await writeFile(path.join(checkout, "variant.patch"), "private patch\n");
    await writeFile(path.join(checkout, "reasoning_tree.yaml"), "private reasoning\n");
    await writeFile(path.join(checkout, "nested/test.patch"), "private test patch\n");
    await writeFile(path.join(checkout, "source/org/example/Prod.java.rej"), "patch reject\n");
    await writeFile(path.join(checkout, "tests/org/example/ProdTest.java.orig"), "patch backup\n");
  }
  return checkout;
}

function topTenProdRanking() {
  return Array.from({ length: 10 }, (_, index) => `${index + 1}. org.example.Prod::m${index}`).join("\n");
}

function topTenPredictionPayload(overrides = {}) {
  const predictions = Array.from({ length: 10 }, (_, index) => ({
    class: "org.example.Prod",
    method: `m${index}`,
  }));
  return { tool: "submit_fault_localization", predictions, ...overrides };
}

function syntheticBenchmarkRecord({
  taskId,
  taskType = "variant",
  runNumber = "run-001",
  status = "completed",
  goldRank = 1,
  files = ["source/org/example/Prod.java"],
  commands = "duration_ms: 1234\n",
} = {}) {
  const metrics = {
    tool_call_count: 10,
    search_count: 4,
    file_read_count: files.length,
    unique_files_read: files.length,
    production_files_read: files.filter((file) => file.startsWith("source/")).length,
    test_files_read: files.filter((file) => file.startsWith("tests/")).length,
    test_run_count: 1,
    gold_file_read: true,
    first_gold_file_read_position: 2,
    files: files.map((file, index) => ({
      file,
      type: file.startsWith("tests/") ? "test" : "production",
      read_count: 1,
      first_read_position: index + 1,
      contains_gold_method: index === 0,
    })),
  };
  return {
    id: `mini-swe-agent-openai-gpt-5-6__${taskId}__${runNumber}`,
    artifact_path: `benchmark_runs/mini-swe-agent-openai-gpt-5-6/${taskId}/${runNumber}/`,
    commands,
    files: metrics.files,
    manifest: {
      id: `mini-swe-agent-openai-gpt-5-6__${taskId}__${runNumber}`,
      run_id: runNumber,
      task_id: taskId,
      task_type: taskType,
      agent: {
        agent_id: "mini-swe-agent-openai-gpt-5-6",
        display_name: "mini-swe / GPT-5.6",
        model: "gpt-5.6",
      },
      status,
      metrics,
      started_at: `2026-09-02T08:00:${runNumber.slice(-2)}Z`,
      completed_at: `2026-09-02T08:00:${runNumber.slice(-2)}Z`,
    },
    evaluation: {
      gold_rank: status === "completed" ? goldRank : null,
      hit_at_5: status === "completed" ? goldRank <= 5 : null,
      hit_at_10: status === "completed" ? goldRank <= 10 : null,
    },
    ranking: { predictions: [] },
    trajectory: [],
    test_runs: [],
  };
}

async function pythonExecutable() {
  const candidates = [process.env.PYTHON, "/opt/miniconda3/bin/python", "python3", "python"].filter(Boolean);
  for (const candidate of candidates) {
    try {
      await execFileAsync(candidate, ["-c", "import minisweagent"], { timeout: 10000 });
      return candidate;
    } catch {
      // Try the next interpreter.
    }
  }
  throw new Error("No Python interpreter with mini-swe-agent available");
}

async function runFaultLocalizationSubmissionValidation(root, action) {
  const catalogPath = path.join(root, "method_catalog.json");
  const submissionPath = path.join(root, "fault-localization-submission.json");
  const actionPath = path.join(root, "submission-action.json");
  await writeFakeChartCheckout(path.join(root, "workspaces", "defects4j"), "buggy");
  const entries = await buildJavaMethodCatalogEntries(path.join(root, "workspaces", "defects4j", "Chart-1", "buggy"));
  await writeFile(
    catalogPath,
    `${JSON.stringify({ schema_version: "d4j-method-catalog/v1", methods: entries }, null, 2)}\n`,
  );
  await writeFile(actionPath, `${JSON.stringify(action, null, 2)}\n`);
  const script = `
import json
import sys
from pathlib import Path
from minisweagent.exceptions import Submitted
from mini_swe_fault_localization import FaultLocalizationEnvironment

env = FaultLocalizationEnvironment(method_catalog_path=sys.argv[1], submission_output_path=sys.argv[2])
action = json.loads(Path(sys.argv[3]).read_text())
try:
    result = env.execute(action)
    print(json.dumps({"submitted": False, "result": result}))
except Submitted as exc:
    print(json.dumps({
        "submitted": True,
        "messages": exc.messages,
        "submission_path_exists": Path(sys.argv[2]).exists(),
        "submission": json.loads(Path(sys.argv[2]).read_text()),
    }))
`;
  const python = await pythonExecutable();
  const { stdout } = await execFileAsync(python, ["-c", script, catalogPath, submissionPath, actionPath], {
    timeout: 10000,
    env: {
      ...process.env,
      PYTHONPATH: [path.resolve("server", "agents"), process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
      MSWEA_CONFIGURED: "true",
      MSWEA_SILENT_STARTUP: "1",
    },
  });
  return JSON.parse(stdout);
}

async function writeSyntheticVariantArtifacts(variantsRoot, variantId = "SYNTHETIC-VARIANT") {
  const variantDir = path.join(variantsRoot, "synthetic", variantId);
  await fs.mkdir(variantDir, { recursive: true });
  await fs.writeFile(
    path.join(variantDir, "variant.patch"),
    `diff --git a/source/org/example/Prod.java b/source/org/example/Prod.java
--- a/source/org/example/Prod.java
+++ b/source/org/example/Prod.java
@@ -4 +4 @@ public class Prod {
-    public int m0() { return 0; }
+    public int m0() { return 42; }
`,
  );
  await fs.writeFile(
    path.join(variantDir, "test.patch"),
    `diff --git a/tests/org/example/ProdTest.java.orig b/tests/org/example/ProdTest.java.orig
new file mode 100644
--- /dev/null
+++ b/tests/org/example/ProdTest.java.orig
@@ -0,0 +1 @@
+private pre-patch test source
diff --git a/tests/org/example/ProdTest.java b/tests/org/example/ProdTest.java
--- a/tests/org/example/ProdTest.java
+++ b/tests/org/example/ProdTest.java
@@ -4 +4 @@ public class ProdTest {
-    public void testBug() {}
+    public void testBug() { new Prod().m0(); }
`,
  );
  return variantDir;
}

function syntheticVariantTask(checkoutRoot, variantDir, variantId = "SYNTHETIC-VARIANT") {
  return {
    task_id: variantId,
    task_type: "variant",
    source: { project: "Chart", bug_id: 1, variant_id: variantId },
    agent_visible_task: {
      schema_version: "d4j-agent-visible-task/v1",
      task_id: variantId,
      failing_test_identifier: "org.example.ProdTest::testBug",
      failing_test_source: "",
      stack_trace: "junit.framework.AssertionFailedError",
      read_only_buggy_repository_path: path.join(checkoutRoot, "Chart-1", "variant"),
      allowed_test_command: "defects4j test -t org.example.ProdTest::testBug",
      source_immutability: {},
    },
    gold_methods: [{ class: "org.example.Prod", method: "m0", file: "source/org/example/Prod.java" }],
    private_adapter: { variant_dir: variantDir },
  };
}

test("agent profiles are durable, status-derived, and secret-free", async () => {
  await withTempRepo(async ({ benchmarkRoot }) => {
    const env = {};
    const initial = await listAgentProfiles(benchmarkRoot, env);
    assert.equal(initial.length, 3);
    assert.equal(initial[0].status, "not_configured");
    assert.equal(initial[0].defaults.timeout_seconds, 300);

    const saved = await saveAgentProfile(
      benchmarkRoot,
      {
        framework: "mini-swe-agent",
        provider: "openai",
        model: "gpt-test",
        display_name: "mini-swe / GPT Test",
        max_tool_calls: 25,
        max_test_runs: 3,
        timeout_seconds: 300,
      },
      env,
    );
    assert.equal(saved.defaults.max_tool_calls, 25);
    assert.equal(assertNoCredentialFields(saved), true);
    assert.equal(assertNoCredentialFields({ api_key: "nope" }), false);
  });
});

test("OpenAI provider is ready with D4J key and D4J model", () => {
  const env = { D4J_OPENAI_API_KEY: "d4j-secret", D4J_OPENAI_MODEL: "gpt-test" };
  const [profile] = defaultAgentProfiles(env);
  const provider = resolveProviderConfig(profile, env);
  const runtime = withAgentRuntimeStatus(profile, {
    env,
    adapter: { available: true },
  });

  assert.equal(provider.credential_configured, true);
  assert.equal(provider.credential_source, "D4J_OPENAI_API_KEY");
  assert.equal(provider.model_configured, true);
  assert.equal(provider.model, "gpt-test");
  assert.equal(runtime.status, "ready");
  assert.equal(runtime.runtime.provider_ready, true);
});

test("OpenAI provider is ready with standard key fallback and D4J model", () => {
  const env = { OPENAI_API_KEY: "standard-secret", D4J_OPENAI_MODEL: "gpt-test" };
  const [profile] = defaultAgentProfiles(env);
  const runtime = withAgentRuntimeStatus(profile, {
    env,
    adapter: { available: true },
  });

  assert.equal(runtime.runtime.credential_configured, true);
  assert.equal(runtime.runtime.credential_source, "OPENAI_API_KEY");
  assert.equal(runtime.runtime.model_configured, true);
  assert.equal(runtime.status, "ready");
});

test("OpenAI provider is not configured without a key", () => {
  const env = { D4J_OPENAI_MODEL: "gpt-test" };
  const [profile] = defaultAgentProfiles(env);
  const runtime = withAgentRuntimeStatus(profile, {
    env,
    adapter: { available: true },
  });

  assert.equal(runtime.runtime.credential_configured, false);
  assert.equal(runtime.runtime.model_configured, true);
  assert.equal(runtime.runtime.provider_ready, false);
  assert.equal(runtime.status, "not_configured");
});

test("OpenAI provider reports key configured but model missing", () => {
  const env = { D4J_OPENAI_API_KEY: "d4j-secret" };
  const [profile] = defaultAgentProfiles(env);
  const provider = resolveProviderConfig(profile, env);
  const runtime = withAgentRuntimeStatus(profile, {
    env,
    adapter: { available: true },
  });

  assert.equal(provider.credential_configured, true);
  assert.equal(provider.model_configured, false);
  assert.equal(provider.provider_ready, false);
  assert.equal(runtime.runtime.provider_ready, false);
  assert.equal(runtime.status, "not_configured");
});

test("OpenAI provider is not ready when adapter is unavailable", () => {
  const env = { D4J_OPENAI_API_KEY: "d4j-secret", D4J_OPENAI_MODEL: "gpt-test" };
  const [profile] = defaultAgentProfiles(env);
  const runtime = withAgentRuntimeStatus(profile, {
    env,
    adapter: { available: false },
  });

  assert.equal(runtime.runtime.credential_configured, true);
  assert.equal(runtime.runtime.model_configured, true);
  assert.equal(runtime.runtime.adapter_available, false);
  assert.equal(runtime.runtime.provider_ready, false);
  assert.equal(runtime.status, "not_configured");
});

test("OpenAI provider diagnostics never expose secret values", () => {
  const env = {
    D4J_OPENAI_API_KEY: "d4j-secret-never-return",
    OPENAI_API_KEY: "standard-secret-never-return",
    D4J_OPENAI_MODEL: "gpt-test",
  };
  const [profile] = defaultAgentProfiles(env);
  const provider = resolveProviderConfig(profile, env);
  const runtime = withAgentRuntimeStatus(profile, {
    env,
    adapter: { available: true },
  });
  const serialized = JSON.stringify({ provider, runtime });

  assert.doesNotMatch(serialized, /d4j-secret-never-return/);
  assert.doesNotMatch(serialized, /standard-secret-never-return/);
  assert.equal(provider.credential_source, "D4J_OPENAI_API_KEY");
});

test("runtime readiness overrides a persisted not-configured profile", async () => {
  await withTempRepo(async ({ benchmarkRoot }) => {
    const persisted = await listAgentProfiles(benchmarkRoot, {});
    assert.equal(persisted[0].status, "not_configured");

    const env = { D4J_OPENAI_API_KEY: "d4j-secret", D4J_OPENAI_MODEL: "gpt-test" };
    const [profile] = await listAgentProfiles(benchmarkRoot, env);
    const runtime = withAgentRuntimeStatus(profile, {
      env,
      adapter: { available: true },
    });

    assert.equal(profile.status, "configured");
    assert.equal(runtime.status, "ready");
    assert.equal(runtime.model, "gpt-test");
    assert.equal(runtime.runtime.provider_ready, true);
  });
});

test("mini-swe runtime model names include the OpenAI provider prefix", () => {
  assert.equal(
    miniSweRuntimeModelName({ provider: "openai", model: "gpt-test" }, { provider: "openai", model: "gpt-test" }),
    "openai/gpt-test",
  );
  assert.equal(
    miniSweRuntimeModelName({ provider: "openai", model: "openai/gpt-test" }, { provider: "openai", model: "openai/gpt-test" }),
    "openai/gpt-test",
  );
});

test("localization prompt requires structured submission instead of plain text final answer", () => {
  assert.match(LOCALIZATION_SYSTEM_PROMPT, /submit_fault_localization tool/);
  assert.match(LOCALIZATION_SYSTEM_PROMPT, /Do not propose a patch/);
  assert.doesNotMatch(LOCALIZATION_SYSTEM_PROMPT, /Output only:\s*1\./);
  assert.doesNotMatch(LOCALIZATION_SYSTEM_PROMPT, /numbered output/i);
  const rendered = renderLocalizationPrompt({
    failing_test_identifier: "org.example.ProdTest::testBug",
    read_only_buggy_repository_path: "/tmp/repo",
    allowed_test_command: "defects4j test -t org.example.ProdTest::testBug",
    failing_test_source: "public void testBug() {}",
    stack_trace: "AssertionError",
  });
  assert.match(rendered, /call submit_fault_localization/);
  assert.doesNotMatch(rendered, /numbered output/i);
});

test("fault-localization submission accepts exactly 10 production methods and terminates cleanly", async () => {
  await withTempRepo(async ({ root }) => {
    const result = await runFaultLocalizationSubmissionValidation(root, topTenPredictionPayload());

    assert.equal(result.submitted, true);
    assert.equal(result.submission_path_exists, true);
    assert.equal(result.submission.ok, true);
    assert.equal(result.submission.predictions.length, 10);
    assert.equal(result.submission.predictions[0].class, "org.example.Prod");
    assert.equal(result.submission.predictions[0].method, "m0");
  });
});

test("fault-localization submission rejects fewer than 10 methods", async () => {
  await withTempRepo(async ({ root }) => {
    const action = topTenPredictionPayload({ predictions: topTenPredictionPayload().predictions.slice(0, 9) });
    const result = await runFaultLocalizationSubmissionValidation(root, action);
    const payload = JSON.parse(result.result.output);

    assert.equal(result.submitted, false);
    assert.equal(result.result.returncode, 1);
    assert.equal(payload.ok, false);
    assert.equal(payload.errors.some((error) => error.code === "invalid_count"), true);
  });
});

test("fault-localization submission rejects more than 10 methods", async () => {
  await withTempRepo(async ({ root }) => {
    const action = topTenPredictionPayload({
      predictions: [...topTenPredictionPayload().predictions, { class: "org.example.Prod", method: "m9" }],
    });
    const result = await runFaultLocalizationSubmissionValidation(root, action);
    const payload = JSON.parse(result.result.output);

    assert.equal(result.submitted, false);
    assert.equal(payload.errors.some((error) => error.code === "invalid_count"), true);
  });
});

test("fault-localization submission rejects duplicate methods", async () => {
  await withTempRepo(async ({ root }) => {
    const predictions = topTenPredictionPayload().predictions;
    predictions[9] = { class: "org.example.Prod", method: "m8" };
    const result = await runFaultLocalizationSubmissionValidation(root, topTenPredictionPayload({ predictions }));
    const payload = JSON.parse(result.result.output);

    assert.equal(result.submitted, false);
    assert.equal(payload.errors.some((error) => error.code === "duplicate_method"), true);
  });
});

test("fault-localization submission rejects test methods", async () => {
  await withTempRepo(async ({ root }) => {
    const predictions = topTenPredictionPayload().predictions;
    predictions[0] = { class: "org.example.ProdTest", method: "testBug" };
    const result = await runFaultLocalizationSubmissionValidation(root, topTenPredictionPayload({ predictions }));
    const payload = JSON.parse(result.result.output);

    assert.equal(result.submitted, false);
    assert.equal(payload.errors.some((error) => error.code === "test_method"), true);
  });
});

test("fault-localization submission rejects nonexistent production methods", async () => {
  await withTempRepo(async ({ root }) => {
    const predictions = topTenPredictionPayload().predictions;
    predictions[0] = { class: "org.example.Prod", method: "missingMethod" };
    const result = await runFaultLocalizationSubmissionValidation(root, topTenPredictionPayload({ predictions }));
    const payload = JSON.parse(result.result.output);

    assert.equal(result.submitted, false);
    assert.equal(payload.errors.some((error) => error.code === "method_not_found"), true);
  });
});

test("fault-localization submission returns structured error for malformed tool payload", async () => {
  await withTempRepo(async ({ root }) => {
    const result = await runFaultLocalizationSubmissionValidation(root, {
      tool: "submit_fault_localization",
      payload_error: "Error parsing tool call arguments: invalid JSON.",
      predictions: null,
    });
    const payload = JSON.parse(result.result.output);

    assert.equal(result.submitted, false);
    assert.equal(payload.errors.some((error) => error.code === "malformed_payload"), true);
    assert.equal(payload.errors.some((error) => error.code === "invalid_schema"), true);
  });
});

test("production method catalog ignores class and method text in Java comments", async () => {
  await withTempRepo(async ({ root }) => {
    const sourceRoot = path.join(root, "workspace");
    await writeFile(
      path.join(sourceRoot, "source/org/example/Prod.java"),
      `package org.example;

/**
 * A comment mentioning class that and public void ghost() {}
 */
public class Prod {
    public void m0() {}
}
`,
    );
    const entries = await buildJavaMethodCatalogEntries(sourceRoot);

    assert.deepEqual(entries.map((entry) => entry.qualified), ["org.example.Prod::m0"]);
  });
});

test("provider-not-configured benchmark run writes canonical artifacts without fake predictions", async () => {
  await withTempRepo(async ({ root, benchmarkRoot, checkoutRoot }) => {
    const [agent] = defaultAgentProfiles({});
    const taskBundle = buildOriginalAgentTask({
      project: "Chart",
      bugId: "1",
      checkoutRoot,
      meta: { triggeringTests: ["org.example.Test::testBug"] },
    });
    const detail = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle, budget: agent.defaults });
    const records = await discoverBenchmarkRunRecords(benchmarkRoot, root);

    assert.equal(records.length, 1);
    assert.equal(detail.manifest.status, "provider_not_configured");
    assert.equal(detail.ranking.predictions.length, 0);
    assert.equal(detail.evaluation.status, "provider_not_configured");
    assert.equal(detail.evaluation.gold_rank, null);
    assert.match(detail.artifact_path, /benchmark_runs\/mini-swe-gpt56\/Chart-1\/run-001\/$/);
  });
});

test("invalid finalization runs are excluded from Hit@5 and Hit@10 aggregation", async () => {
  await withTempRepo(async ({ root, benchmarkRoot, checkoutRoot }) => {
    await writeFakeChartCheckout(checkoutRoot, "buggy");
    const [agent] = defaultAgentProfiles({ OPENAI_API_KEY: "configured-for-test", D4J_OPENAI_MODEL: "gpt-test" });
    const taskBundle = buildOriginalAgentTask({
      project: "Chart",
      bugId: "1",
      checkoutRoot,
      meta: { triggeringTests: ["org.example.ProdTest::testBug"], modifiedClasses: ["org.example.Prod"] },
    });
    const adapter = {
      async prepareRun() {
        return {
          workspace_repo: path.join(checkoutRoot, "Chart-1", "buggy"),
          agent_visible_task: taskBundle.agent_visible_task,
          workspace_manifest: {
            private_metadata_scan: { ok: true },
          },
          method_catalog: new Set(topTenPredictionPayload().predictions.map((prediction) => `${prediction.class}::${prediction.method}`)),
        };
      },
      async execute() {
        return {
          status: "completed",
          status_reason: "agent attempted malformed structured finalization",
          provider_config: { provider: "openai", status: "configured", configured: true },
          adapter: { framework: "mini-swe-agent", available: true, path: "/tmp/mini", source: "test" },
          raw_output: "structured submission attempt",
          commands: "$ mini-swe-agent\n",
          trajectory: [{ sequence: 1, type: "submission", target: "submit_fault_localization", metadata: { prediction_count: 9 } }],
          test_runs: [],
          ranking_payload: { predictions: topTenPredictionPayload().predictions.slice(0, 9) },
          structured_submission: {
            schema_version: "d4j-fl-submission/v1",
            ok: false,
            predictions: topTenPredictionPayload().predictions.slice(0, 9),
          },
        };
      },
    };
    const detail = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle, budget: agent.defaults, adapter });

    assert.equal(detail.manifest.status, "invalid_ranking");
    assert.equal(detail.ranking.parse_status, "invalid");
    assert.equal(detail.evaluation.gold_rank, null);
    assert.equal(detail.evaluation.hit_at_5, null);
    assert.equal(detail.evaluation.hit_at_10, null);
  });
});

test("timeout benchmark run preserves artifacts and excludes hit aggregation", async () => {
  await withTempRepo(async ({ root, benchmarkRoot, checkoutRoot }) => {
    await writeFakeChartCheckout(checkoutRoot, "buggy");
    const [agent] = defaultAgentProfiles({ OPENAI_API_KEY: "configured-for-test", D4J_OPENAI_MODEL: "gpt-test" });
    const taskBundle = buildOriginalAgentTask({
      project: "Chart",
      bugId: "1",
      checkoutRoot,
      meta: { triggeringTests: ["org.example.ProdTest::testBug"], modifiedClasses: ["org.example.Prod"] },
    });
    const adapter = {
      async prepareRun() {
        return {
          workspace_repo: path.join(checkoutRoot, "Chart-1", "buggy"),
          agent_visible_task: taskBundle.agent_visible_task,
          workspace_manifest: {
            private_metadata_scan: { ok: true },
          },
          method_catalog: null,
        };
      },
      async execute() {
        return {
          status: "timeout",
          status_reason: "mini-swe-agent exceeded the 300-second benchmark execution timeout.",
          provider_config: { provider: "openai", status: "configured", configured: true },
          adapter: { framework: "mini-swe-agent", available: true, path: "/tmp/mini", source: "test" },
          raw_output: "partial agent output preserved",
          commands: "$ mini-swe-agent\nexecution_timeout_seconds: 300\ntimed_out: true\n",
          trajectory: [
            { sequence: 1, type: "search", target: "getLegendItem", metadata: {} },
            { sequence: 2, type: "open_file", target: "source/org/example/Prod.java", metadata: {} },
            { sequence: 3, type: "test_run", target: "org.example.ProdTest::testBug", metadata: {} },
          ],
          test_runs: [{ test_id: "org.example.ProdTest::testBug", run_number: 1, status: "recorded", output: "failure" }],
          ranking_text: topTenProdRanking(),
          timeouts: {
            agent_startup_seconds: MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS,
            benchmark_execution_seconds: 300,
            execution_timer_starts: "after mini-swe-agent process launch for the fault-localization task",
          },
        };
      },
    };

    const detail = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle, budget: agent.defaults, adapter });

    assert.equal(detail.manifest.status, "timeout");
    assert.equal(detail.manifest.timeouts.agent_startup_seconds, MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS);
    assert.equal(detail.manifest.timeouts.benchmark_execution_seconds, 300);
    assert.equal(detail.ranking.parse_status, "not_run");
    assert.equal(detail.ranking.predictions.length, 0);
    assert.equal(detail.evaluation.gold_rank, null);
    assert.equal(detail.evaluation.hit_at_5, null);
    assert.equal(detail.evaluation.hit_at_10, null);
    assert.equal(detail.manifest.metrics.tool_call_count, 3);
    assert.equal(detail.test_runs.length, 1);
    assert.match(detail.raw_output, /partial agent output preserved/);
  });
});

test("mini-swe adapter creates isolated provider-not-configured workspaces", async () => {
  await withTempRepo(async ({ root, benchmarkRoot, checkoutRoot, variantsRoot }) => {
    await writeFakeChartCheckout(checkoutRoot, "buggy", { privateFiles: true });
    const [agent] = defaultAgentProfiles({});
    const adapter = new MiniSweAgentAdapter({ repoRoot: root, checkoutRoot, variantsRoot, env: {} });
    const taskBundle = buildOriginalAgentTask({
      project: "Chart",
      bugId: "1",
      checkoutRoot,
      meta: { triggeringTests: ["org.example.ProdTest::testBug"], modifiedClasses: ["org.example.Prod"] },
    });
    const detail = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle, budget: agent.defaults, adapter });
    const workspaceRepo = detail.task.read_only_buggy_repository_path;

    assert.equal(detail.manifest.status, "provider_not_configured");
    assert.match(workspaceRepo, /benchmark_runs\/mini-swe-gpt56\/Chart-1\/run-001\/workspace\/Chart-1b$/);
    assert.equal(await fs.stat(workspaceRepo).then((stat) => stat.isDirectory()), true);
    await assert.rejects(() => fs.stat(path.join(workspaceRepo, ".git")));
    await assert.rejects(() => fs.stat(path.join(workspaceRepo, ".svn")));
    await assert.rejects(() => fs.stat(path.join(workspaceRepo, "variant.patch")));
    await assert.rejects(() => fs.stat(path.join(workspaceRepo, "reasoning_tree.yaml")));
    await assert.rejects(() => fs.stat(path.join(workspaceRepo, "nested/test.patch")));
    await assert.rejects(() => fs.stat(path.join(workspaceRepo, "source/org/example/Prod.java.rej")));
    await assert.rejects(() => fs.stat(path.join(workspaceRepo, "tests/org/example/ProdTest.java.orig")));
    assert.equal(detail.manifest.isolation.private_metadata_inaccessible, true);
    assert.equal(detail.manifest.integrity.ok, true);
    assert.equal(detail.manifest.prompt.version, "d4j-localization-only/v2");
  });
});

test("mini-swe adapter enforces execution timeout and preserves partial output", async () => {
  await withTempRepo(async ({ root, checkoutRoot, variantsRoot }) => {
    await writeFakeChartCheckout(checkoutRoot, "buggy");
    const fakeMiniSweAgent = path.join(root, "fake-mini-swe-agent.mjs");
    await writeFile(
      fakeMiniSweAgent,
      `#!/usr/bin/env node
if (process.argv.includes("--version")) {
  console.log("mini-swe-agent fake 2.4.6");
  process.exit(0);
}
const modelIndex = process.argv.indexOf("--model");
console.log("runtime_model=" + process.argv[modelIndex + 1]);
console.log("configured=" + process.env.MSWEA_CONFIGURED);
setTimeout(() => console.log("done"), 2000);
`,
    );
    await fs.chmod(fakeMiniSweAgent, 0o755);

    const env = {
      D4J_OPENAI_API_KEY: "configured-for-test",
      D4J_OPENAI_MODEL: "gpt-test",
      MINI_SWE_AGENT_BIN: fakeMiniSweAgent,
      PATH: process.env.PATH ?? "",
    };
    const [agent] = defaultAgentProfiles(env);
    const adapter = new MiniSweAgentAdapter({ repoRoot: root, checkoutRoot, variantsRoot, env });
    const taskBundle = buildOriginalAgentTask({
      project: "Chart",
      bugId: "1",
      checkoutRoot,
      meta: { triggeringTests: ["org.example.ProdTest::testBug"], modifiedClasses: ["org.example.Prod"] },
    });
    const runDir = path.join(root, "benchmark_runs", agent.agent_id, taskBundle.task_id, "run-001");
    await fs.mkdir(runDir, { recursive: true });
    const prepared = await adapter.prepareRun({ runDir, taskBundle, agent, budget: agent.defaults });

    const result = await adapter.execute({
      runDir,
      agent,
      budget: { max_tool_calls: 50, max_test_runs: 5, timeout_seconds: 0.5 },
      prepared,
      renderedPrompt: "Smoke-test timeout preservation.",
    });

    assert.equal(result.status, "timeout");
    assert.equal(result.ranking_text, "");
    assert.match(result.raw_output, /runtime_model=openai\/gpt-test/);
    assert.match(result.raw_output, /configured=true/);
    assert.doesNotMatch(result.raw_output, /configured-for-test/);
    assert.equal(result.timeouts.agent_startup_seconds, MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS);
    assert.equal(result.timeouts.benchmark_execution_seconds, 0.5);
    assert.match(result.commands, /timed_out: true/);
  });
});

test("workspace isolation scan classifies patch backups separately from git history", async () => {
  await withTempRepo(async ({ root }) => {
    await writeFile(path.join(root, "tests/org/example/ProdTest.java.orig"), "backup\n");
    const scan = await scanPrivateMetadata(root);

    assert.equal(scan.ok, false);
    assert.equal(scan.patch_backup_leak, true);
    assert.equal(scan.git_history_leak, false);
    assert.equal(scan.private_benchmark_metadata_leak, false);
    assert.deepEqual(scan.leaks.map((leak) => [leak.path, leak.category]), [
      ["tests/org/example/ProdTest.java.orig", "patch_backup_leak"],
    ]);
  });
});

test("workspace isolation scan rejects patch rejects, git history, and reasoning metadata with distinct categories", async () => {
  await withTempRepo(async ({ root }) => {
    await writeFile(path.join(root, "source/org/example/Prod.java.rej"), "reject\n");
    await writeFile(path.join(root, ".git/config"), "history\n");
    await writeFile(path.join(root, "reasoning_tree.yaml"), "private reasoning\n");
    const scan = await scanPrivateMetadata(root);

    assert.equal(scan.ok, false);
    assert.equal(scan.patch_backup_leak, true);
    assert.equal(scan.git_history_leak, true);
    assert.equal(scan.private_benchmark_metadata_leak, true);
    assert.deepEqual(
      scan.leaks.map((leak) => leak.category).sort(),
      ["git_history_leak", "patch_backup_leak", "private_benchmark_metadata_leak"],
    );
  });
});

test("variant staging removes patch-created backups before final agent workspace hashing", async () => {
  await withTempRepo(async ({ root, checkoutRoot, variantsRoot }) => {
    await writeFakeChartCheckout(checkoutRoot, "fixed");
    const variantDir = await writeSyntheticVariantArtifacts(variantsRoot);
    const adapter = new MiniSweAgentAdapter({ repoRoot: root, checkoutRoot, variantsRoot, env: {} });
    const runDir = path.join(root, "benchmark_runs", "agent", "SYNTHETIC-VARIANT", "run-001");
    const prepared = await adapter.prepareRun({
      runDir,
      taskBundle: syntheticVariantTask(checkoutRoot, variantDir),
    });

    assert.equal(prepared.workspace_manifest.private_metadata_scan.ok, true);
    assert.equal(prepared.workspace_manifest.staging_sanitization.removed_entries[0].path, "tests/org/example/ProdTest.java.orig");
    assert.equal(prepared.workspace_manifest.staging_sanitization.removed_entries[0].category, "patch_backup_leak");
    await assert.rejects(() => fs.stat(path.join(prepared.workspace_repo, "tests/org/example/ProdTest.java.orig")));
    assert.match(await fs.readFile(path.join(prepared.workspace_repo, "tests/org/example/ProdTest.java"), "utf8"), /new Prod\(\)\.m0/);
    assert.match(await fs.readFile(path.join(prepared.workspace_repo, "source/org/example/Prod.java"), "utf8"), /return 42/);
    assert.equal(prepared.source_hashes_before.files.some((file) => file.path.endsWith(".orig")), false);
    assert.equal(prepared.source_hashes_before.files.some((file) => file.path === "tests/org/example/ProdTest.java"), true);
  });
});

test("agent launch is blocked when prepared workspace isolation fails", async () => {
  await withTempRepo(async ({ root, benchmarkRoot }) => {
    let executed = false;
    const [agent] = defaultAgentProfiles({ OPENAI_API_KEY: "configured-for-test" });
    const taskBundle = {
      task_id: "LEAKY-TASK",
      task_type: "original",
      source: { project: "Chart", bug_id: 1 },
      agent_visible_task: {
        schema_version: "d4j-agent-visible-task/v1",
        task_id: "LEAKY-TASK",
        failing_test_identifier: "org.example.ProdTest::testBug",
        failing_test_source: "public void testBug() {}",
        stack_trace: "failure",
        read_only_buggy_repository_path: path.join(root, "workspace"),
        allowed_test_command: "defects4j test -t org.example.ProdTest::testBug",
        source_immutability: {},
      },
      gold_methods: [],
    };
    const adapter = {
      async prepareRun() {
        return {
          workspace_repo: path.join(root, "workspace"),
          agent_visible_task: taskBundle.agent_visible_task,
          workspace_manifest: {
            private_metadata_scan: {
              ok: false,
              git_history_leak: false,
              patch_backup_leak: true,
              private_benchmark_metadata_leak: false,
              fixed_revision_leak: false,
              unexpected_artifact_leak: false,
              banned_entries: ["tests/org/example/ProdTest.java.orig"],
            },
          },
          method_catalog: null,
        };
      },
      async execute() {
        executed = true;
        return { status: "completed", ranking_text: topTenProdRanking(), trajectory: [], test_runs: [] };
      },
    };
    const detail = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle, budget: agent.defaults, adapter });

    assert.equal(executed, false);
    assert.equal(detail.manifest.status, "protocol_violation");
    assert.match(detail.manifest.status_reason, /Agent-visible workspace contains private benchmark metadata|isolation failed/);
    assert.equal(detail.manifest.workspace.private_metadata_scan.patch_backup_leak, true);
  });
});

test("source hash integrity detects changed production or test sources", async () => {
  await withTempRepo(async ({ checkoutRoot }) => {
    const checkout = await writeFakeChartCheckout(checkoutRoot, "buggy");
    const before = await hashSourceFiles(checkout);
    await fs.appendFile(path.join(checkout, "source/org/example/Prod.java"), "\n// mutation\n");
    const after = await hashSourceFiles(checkout);
    const comparison = compareSourceHashes(before, after);

    assert.equal(comparison.ok, false);
    assert.deepEqual(
      comparison.changed_files.map((file) => [file.path, file.change]),
      [["source/org/example/Prod.java", "modified"]],
    );
  });
});

test("source hashing and method catalog include nested project source roots", async () => {
  await withTempRepo(async ({ root }) => {
    const production = path.join(root, "gson/src/main/java/com/google/gson/Nested.java");
    const testSource = path.join(root, "gson/src/test/java/com/google/gson/NestedTest.java");
    await fs.mkdir(path.dirname(production), { recursive: true });
    await fs.mkdir(path.dirname(testSource), { recursive: true });
    await fs.writeFile(production, "package com.google.gson; public class Nested { public Nested() {} public void resolve() {} }\n");
    await fs.writeFile(testSource, "package com.google.gson; public class NestedTest { public void testResolve() {} }\n");

    const hashes = await hashSourceFiles(root);
    assert.deepEqual(
      hashes.files.map((entry) => entry.path),
      [
        "gson/src/main/java/com/google/gson/Nested.java",
        "gson/src/test/java/com/google/gson/NestedTest.java",
      ],
    );
    const catalog = await buildJavaMethodCatalogEntries(root);
    assert.equal(catalog.some((entry) => entry.qualified === "com.google.gson.Nested::resolve"), true);
    assert.equal(catalog.some((entry) => entry.class.endsWith("NestedTest")), false);
  });
});

test("signature-qualified constructor metadata normalizes without weakening method validation", () => {
  assert.equal(
    normalizeJavaMethodIdentity("Partial(DateTimeFieldType[], int[], Chronology)"),
    "Partial",
  );
  assert.equal(normalizeJavaMethodIdentity("getActualType"), "getActualType");
  assert.equal(normalizeJavaMethodIdentity("Partial(DateTimeFieldType[]"), null);
  assert.equal(normalizeJavaMethodIdentity("Partial(DateTimeFieldType[)"), null);
  assert.equal(normalizeJavaMethodIdentity("Partial)()"), null);
});

test("reasoning-node evidence accepts non-empty scalar or list transport", () => {
  assert.equal(hasRequiredEvidence("failing test and source branch"), true);
  assert.equal(hasRequiredEvidence(["failing test", "source branch"]), true);
  assert.equal(hasRequiredEvidence([]), false);
  assert.equal(hasRequiredEvidence(["failing test", ""]), false);
  assert.equal(hasRequiredEvidence(""), false);
});

test("benchmark run is marked protocol_violation when an adapter mutates source", async () => {
  await withTempRepo(async ({ root, benchmarkRoot, checkoutRoot, variantsRoot }) => {
    await writeFakeChartCheckout(checkoutRoot, "buggy");
    class MutatingAdapter extends MiniSweAgentAdapter {
      async execute({ prepared }) {
        await fs.appendFile(path.join(prepared.workspace_repo, "source/org/example/Prod.java"), "\n// illegal repair\n");
        return {
          status: "completed",
          status_reason: "fake completed run for integrity test",
          provider_config: { provider: "openai", status: "configured", configured: true },
          adapter: { framework: "mini-swe-agent", available: true, path: "/tmp/mini", source: "test" },
          raw_output: topTenProdRanking(),
          commands: "$ mini-swe-agent\n",
          trajectory: [{ sequence: 1, type: "open_file", target: "source/org/example/Prod.java", metadata: {} }],
          test_runs: [],
          ranking_text: topTenProdRanking(),
        };
      }
    }
    const [agent] = defaultAgentProfiles({ OPENAI_API_KEY: "configured-for-test" });
    const adapter = new MutatingAdapter({ repoRoot: root, checkoutRoot, variantsRoot, env: { OPENAI_API_KEY: "configured-for-test" } });
    const taskBundle = buildOriginalAgentTask({
      project: "Chart",
      bugId: "1",
      checkoutRoot,
      meta: { triggeringTests: ["org.example.ProdTest::testBug"], modifiedClasses: ["org.example.Prod"] },
    });
    const detail = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle, budget: agent.defaults, adapter });

    assert.equal(detail.manifest.status, "protocol_violation");
    assert.equal(detail.manifest.integrity.ok, false);
    assert.equal(detail.manifest.integrity.changed_files[0].path, "source/org/example/Prod.java");
    assert.equal(detail.ranking.parse_status, "parsed");
  });
});

test("mini-swe adapter rejects variant artifact path traversal", async () => {
  await withTempRepo(async ({ root, benchmarkRoot, checkoutRoot, variantsRoot }) => {
    await writeFakeChartCheckout(checkoutRoot, "fixed");
    const [agent] = defaultAgentProfiles({});
    const adapter = new MiniSweAgentAdapter({ repoRoot: root, checkoutRoot, variantsRoot, env: {} });
    const taskBundle = {
      task_id: "BAD-VARIANT",
      task_type: "variant",
      source: { project: "Chart", bug_id: 1, variant_id: "BAD-VARIANT" },
      agent_visible_task: {
        task_id: "BAD-VARIANT",
        failing_test_identifier: "org.example.ProdTest::testBug",
        failing_test_source: "",
        stack_trace: "",
        read_only_buggy_repository_path: path.join(checkoutRoot, "Chart-1", "variant"),
        allowed_test_command: "defects4j test -t org.example.ProdTest::testBug",
        source_immutability: {},
      },
      gold_methods: [],
      private_adapter: { variant_dir: path.join(root, "..", "outside") },
    };

    const detail = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle, budget: agent.defaults, adapter });
    assert.equal(detail.manifest.status, "failed");
    assert.match(detail.manifest.status_reason, /outside the allowed root/);
  });
});

test("trajectory normalization captures observable mini-swe-agent commands", () => {
  const events = normalizeTrajectoryEvents(
    {
      messages: [
        { role: "assistant", extra: { actions: [{ command: "rg getLegendItem source" }] } },
        { role: "assistant", extra: { actions: [{ command: "nl -ba source/org/example/Prod.java | sed -n '1,40p'" }] } },
        { role: "assistant", extra: { actions: [{ command: "defects4j test -t org.example.ProdTest::testBug" }] } },
      ],
    },
    "/tmp/repo",
  );

  assert.deepEqual(
    events.map((event) => event.type),
    ["search", "open_file", "test_run"],
  );
  assert.equal(events[1].target, "source/org/example/Prod.java");
});

test("variant task isolation excludes gold, patches, reasoning trees, and reports", async () => {
  await withTempRepo(async ({ variantsRoot, runsRoot, checkoutRoot }) => {
    const migration = await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const taskBundle = buildVariantAgentTask({ record: migration.record, checkoutRoot });
    const isolation = assertAgentTaskIsolation(taskBundle.agent_visible_task);
    const serializedTask = JSON.stringify(taskBundle.agent_visible_task);

    assert.equal(isolation.ok, true);
    assert.doesNotMatch(serializedTask, /gold|variant\.patch|reasoning_tree|variant_report|fixed_revision/i);
    assert.equal(taskBundle.gold_methods[0].method, "getLegendItem");
  });
});

test("Top-10 parser accepts ranked production methods and rejects duplicates/test methods", () => {
  const valid = {
    predictions: Array.from({ length: 10 }, (_, index) => ({
      rank: index + 1,
      class: `org.example.Prod${index}`,
      method: `method${index}`,
    })),
  };
  assert.equal(parseTopTenRanking(valid).ok, true);

  const duplicate = {
    predictions: Array.from({ length: 10 }, (_, index) => ({
      rank: index + 1,
      class: "org.example.Prod",
      method: index === 9 ? "method8" : `method${index}`,
    })),
  };
  assert.equal(parseTopTenRanking(duplicate).ok, false);

  const testMethod = {
    predictions: Array.from({ length: 10 }, (_, index) => ({
      rank: index + 1,
      class: index === 0 ? "org.example.SomeTest" : `org.example.Prod${index}`,
      method: index === 0 ? "testFailure" : `method${index}`,
    })),
  };
  assert.equal(parseTopTenRanking(testMethod).ok, false);
});

test("Hit@5 and Hit@10 evaluation supports multiple gold methods", () => {
  const predictions = Array.from({ length: 10 }, (_, index) => ({
    rank: index + 1,
    class: `org.example.C${index}`,
    method: `m${index}`,
  }));
  const hitAt5 = evaluateRanking(predictions, [{ class: "org.example.C4", method: "m4" }]);
  const hitAt10 = evaluateRanking(predictions, [{ class: "org.example.C8", method: "m8" }]);

  assert.equal(hitAt5.gold_rank, 5);
  assert.equal(hitAt5.hit_at_5, true);
  assert.equal(hitAt10.gold_rank, 9);
  assert.equal(hitAt10.hit_at_5, false);
  assert.equal(hitAt10.hit_at_10, true);
});

test("behavior metrics and file overlap are computed from observable trajectory only", () => {
  const metrics = computeBehaviorMetrics(
    [
      { sequence: 1, type: "search", target: "getLegendItem" },
      { sequence: 2, type: "open_file", target: "source/A.java" },
      { sequence: 3, type: "open_file", target: "tests/ATest.java" },
      { sequence: 4, type: "open_file", target: "source/A.java" },
      { sequence: 5, type: "test_run", target: "A::test" },
    ],
    [{ class: "A", method: "m", file: "source/A.java" }],
  );
  const overlap = fileOverlap(["source/A.java", "source/B.java"], ["source/A.java", "source/C.java"]);

  assert.equal(metrics.tool_call_count, 5);
  assert.equal(metrics.unique_files_read, 2);
  assert.equal(metrics.gold_file_read, true);
  assert.equal(overlap.jaccard, 1 / 3);
  assert.deepEqual(overlap.shared_files, ["source/A.java"]);
});

test("run lookup and artifact reads reject invalid IDs and traversal", async () => {
  await withTempRepo(async ({ root, benchmarkRoot, checkoutRoot }) => {
    const [agent] = defaultAgentProfiles({});
    const taskBundle = buildOriginalAgentTask({
      project: "Chart",
      bugId: "1",
      checkoutRoot,
      meta: { triggeringTests: ["org.example.Test::testBug"] },
    });
    const detail = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle, budget: agent.defaults });
    const found = await findBenchmarkRunById(benchmarkRoot, root, detail.id);

    assert.equal(found.id, detail.id);
    assert.throws(() => sanitizeBenchmarkId("../run-001", "run id"), /Invalid run id/);
    await assert.rejects(() => readBenchmarkArtifact(found, "../task.json"), /Invalid benchmark artifact/);
  });
});

test("pair comparison renders metric rows and file overlap", async () => {
  await withTempRepo(async ({ root, benchmarkRoot, checkoutRoot, variantsRoot, runsRoot }) => {
    const [agent] = defaultAgentProfiles({});
    const original = buildOriginalAgentTask({
      project: "Chart",
      bugId: "1",
      checkoutRoot,
      meta: { triggeringTests: ["org.example.Test::testBug"] },
    });
    const migration = await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
    const variant = buildVariantAgentTask({ record: migration.record, checkoutRoot });
    const originalRun = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle: original, budget: agent.defaults });
    const variantRun = await createBenchmarkRun({ benchmarkRoot, repoRoot: root, agent, taskBundle: variant, budget: agent.defaults });
    const comparison = compareOriginalVariantRuns(originalRun, variantRun);

    assert.equal(comparison.mode, "original_vs_variant");
    assert.equal(comparison.rows.some((row) => row.metric === "Hit@10"), true);
    assert.equal(comparison.file_overlap.jaccard, null);
  });
});

test("benchmark duration is parsed from the command artifact", () => {
  assert.equal(parseBenchmarkDurationMs("duration_ms: 100\n"), 100);
  assert.equal(parseBenchmarkDurationMs("duration_ms: 100\nother\nduration_ms: 250\n"), 250);
  assert.equal(parseBenchmarkDurationMs("no duration"), null);
});

test("Chart depth ladder aggregates completed pilot results and missing levels", () => {
  const records = [
    syntheticBenchmarkRecord({
      taskId: "Chart-1",
      taskType: "original",
      runNumber: "run-005",
      files: [
        "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
        "source/org/jfree/chart/plot/CategoryPlot.java",
      ],
      commands: "duration_ms: 42685\n",
    }),
    syntheticBenchmarkRecord({
      taskId: "CHART-1-L10-SECONDARY-02",
      runNumber: "run-002",
      files: [
        "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
        "source/org/jfree/chart/plot/CategoryPlot.java",
        "source/org/jfree/chart/renderer/category/AreaRenderer.java",
      ],
      commands: "duration_ms: 46453\n",
    }),
  ];
  const variants = [
    {
      variantId: "CHART-1-L10-SECONDARY-02",
      status: "validated",
      manifest: {
        benchmark_eligible: true,
        reasoning: { level: "L10", unit_count: 11, reasoning_level_status: "validated" },
      },
    },
  ];
  const ladder = buildChartDepthLadder(records, variants);
  const original = ladder.rows.find((row) => row.label === "Original");
  const l10 = ladder.rows.find((row) => row.label === "L10");
  const l20 = ladder.rows.find((row) => row.label === "L20");

  assert.equal(original.status, "completed");
  assert.equal(original.duration_ms, 42685);
  assert.equal(l10.semantic_inference_steps, 11);
  assert.equal(l10.duration_ms, 46453);
  assert.equal(l20.status, "not_generated");
  assert.equal(l20.hit_at_5, null);
  assert.equal(ladder.pilot_baseline.file_jaccard, 2 / 3);
  assert.equal(ladder.file_overlap_matrix.pairs.some((pair) => pair.from === "Original" && pair.to === "L10"), true);
});

test("Chart pilot summary exposes UI-ready original and L10 metrics", () => {
  const records = [
    syntheticBenchmarkRecord({
      taskId: "Chart-1",
      taskType: "original",
      runNumber: "run-005",
      files: [
        "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
        "source/org/jfree/chart/plot/CategoryPlot.java",
      ],
      commands: "duration_ms: 42685\n",
    }),
    syntheticBenchmarkRecord({
      taskId: "CHART-1-L10-SECONDARY-02",
      runNumber: "run-002",
      files: [
        "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
        "source/org/jfree/chart/plot/CategoryPlot.java",
        "source/org/jfree/chart/renderer/category/AreaRenderer.java",
      ],
      commands: "duration_ms: 46453\n",
    }),
  ];
  const variants = [
    {
      variantId: "CHART-1-L10-SECONDARY-02",
      status: "validated",
      manifest: {
        benchmark_eligible: true,
        reasoning: { level: "L10", semantic_inference_steps: 11, reasoning_level_status: "validated" },
      },
    },
  ];
  const summary = buildChartDepthLadder(records, variants).pilot_baseline;

  assert.equal(summary.original.run_id, "mini-swe-agent-openai-gpt-5-6__Chart-1__run-005");
  assert.equal(summary.original.status, "completed");
  assert.equal(summary.original.hit_at_5, true);
  assert.equal(summary.original.hit_at_10, true);
  assert.equal(summary.original.duration_ms, 42685);
  assert.equal(summary.l10.run_id, "mini-swe-agent-openai-gpt-5-6__CHART-1-L10-SECONDARY-02__run-002");
  assert.equal(summary.l10.status, "completed");
  assert.equal(summary.l10.semantic_inference_steps, 11);
  assert.equal(summary.l10.hit_at_5, true);
  assert.equal(summary.l10.hit_at_10, true);
  assert.equal(summary.l10.duration_ms, 46453);
  assert.equal(summary.file_jaccard, 2 / 3);
});

test("Chart depth ladder reports failed generated variants without hit aggregation", () => {
  const failed = syntheticBenchmarkRecord({
    taskId: "CHART-1-L20-001",
    status: "timeout",
    goldRank: 1,
    commands: "duration_ms: 300000\n",
  });
  const variants = [
    {
      variantId: "CHART-1-L20-001",
      status: "validated",
      manifest: {
        benchmark_eligible: true,
        reasoning: { level: "L20", semantic_inference_steps: 18, reasoning_level_status: "validated" },
      },
    },
  ];
  const ladder = buildChartDepthLadder([failed], variants);
  const l20 = ladder.rows.find((row) => row.label === "L20");

  assert.equal(l20.status, "timeout");
  assert.equal(l20.reasoning_level_status, "validated");
  assert.equal(l20.gold_rank, null);
  assert.equal(l20.hit_at_5, null);
  assert.equal(l20.hit_at_10, null);
});
