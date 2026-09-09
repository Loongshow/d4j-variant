import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  AgentAdapter,
  buildJavaMethodCatalogEntries,
  compareSourceHashes,
  copyDirectoryFiltered,
  hashSourceFiles,
  normalizeTrajectoryEvents,
  safeResolveWithin,
  sanitizeAgentWorkspace,
  scanPrivateMetadata,
  stripHistoryDirs,
  trajectoryJsonl,
} from "./agentAdapter.mjs";
import { buildProviderEnvironment, resolveProviderConfig } from "./providerConfig.mjs";

const CHART_SECONDARY_VARIANT_ID = "CHART-1-L10-SECONDARY-02";
const installRequirement = "python -m pip install mini-swe-agent==2.4.6";
export const MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS = 30;
export const DEFAULT_BENCHMARK_EXECUTION_TIMEOUT_SECONDS = 300;
const adapterModuleDir = path.dirname(fileURLToPath(import.meta.url));

function runProcess(command, args, options = {}) {
  const started = Date.now();
  const timeoutMs = Number.isFinite(Number(options.timeout)) ? Number(options.timeout) : 30000;
  const killSignal = options.killSignal ?? "SIGTERM";
  return new Promise((resolve) => {
    execFile(
      command,
      args,
      {
        cwd: options.cwd,
        env: options.env,
        timeout: timeoutMs,
        killSignal,
        maxBuffer: options.maxBuffer ?? 20 * 1024 * 1024,
      },
      (error, stdout = "", stderr = "") => {
        const durationMs = Date.now() - started;
        const timedOut = Boolean(
          error &&
            timeoutMs > 0 &&
            (error.killed || /timed out|timeout/i.test(error.message ?? "")) &&
            durationMs >= timeoutMs - 250,
        );
        resolve({
          command,
          args,
          cwd: options.cwd ?? process.cwd(),
          exit_code: typeof error?.code === "number" ? error.code : error ? 1 : 0,
          signal: error?.signal ?? null,
          stdout,
          stderr,
          error: error?.message ?? "",
          duration_ms: durationMs,
          timed_out: timedOut,
          timeout_ms: timeoutMs,
          kill_signal: killSignal,
          started_at: new Date(started).toISOString(),
          timestamp: new Date().toISOString(),
        });
      },
    );
  });
}

async function commandPath(name) {
  const result = await runProcess("sh", ["-lc", `command -v ${name}`], { timeout: 10000 });
  return result.exit_code === 0 ? result.stdout.trim().split(/\r?\n/)[0] : "";
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function redactKnownSecrets(text, env = process.env) {
  let next = String(text ?? "");
  for (const [name, value] of Object.entries(env)) {
    if (!value || !/(api[_-]?key|secret|token|password)/i.test(name)) continue;
    const variants = new Set([
      String(value),
      String(value).trim(),
      String(value).replace(/\s+/g, ""),
    ]);
    for (const secret of variants) {
      if (secret.length < 8) continue;
      next = next.split(secret).join(`[redacted:${name}]`);
      const whitespaceWrapped = secret
        .split("")
        .map((char) => escapeRegExp(char))
        .join("\\s*");
      next = next.replace(new RegExp(whitespaceWrapped, "g"), `[redacted:${name}]`);
    }
  }
  next = next.replace(/sk-proj-[A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+){1,}/g, "[redacted:OPENAI_API_KEY]");
  next = next.replace(/sk-proj-[A-Za-z0-9_-]+(?:\u2026|…)/g, "[redacted:OPENAI_API_KEY]");
  return next;
}

function workspaceLabelForTask(taskBundle) {
  if (taskBundle.task_type === "original") {
    return `${taskBundle.source.project}-${taskBundle.source.bug_id}b`;
  }
  return taskBundle.task_id;
}

function assertInside(root, target, label) {
  const resolvedRoot = path.resolve(root);
  const resolvedTarget = path.resolve(target);
  const rootWithSep = resolvedRoot.endsWith(path.sep) ? resolvedRoot : `${resolvedRoot}${path.sep}`;
  if (resolvedTarget !== resolvedRoot && !resolvedTarget.startsWith(rootWithSep)) {
    throw new Error(`${label} is outside the allowed root`);
  }
  return resolvedTarget;
}

function testIdentifierParts(identifier = "") {
  const [className, methodName] = String(identifier).split("::");
  return {
    className: className ?? "",
    methodName: methodName ?? "",
  };
}

function findMatchingBrace(source, openBraceIndex) {
  let depth = 0;
  let inLineComment = false;
  let inBlockComment = false;
  let inString = false;
  let inChar = false;
  for (let index = openBraceIndex; index < source.length; index += 1) {
    const char = source[index];
    const next = source[index + 1];
    const prev = source[index - 1];
    if (inLineComment) {
      if (char === "\n") inLineComment = false;
      continue;
    }
    if (inBlockComment) {
      if (char === "*" && next === "/") {
        inBlockComment = false;
        index += 1;
      }
      continue;
    }
    if (inString) {
      if (char === "\"" && prev !== "\\") inString = false;
      continue;
    }
    if (inChar) {
      if (char === "'" && prev !== "\\") inChar = false;
      continue;
    }
    if (char === "/" && next === "/") {
      inLineComment = true;
      index += 1;
      continue;
    }
    if (char === "/" && next === "*") {
      inBlockComment = true;
      index += 1;
      continue;
    }
    if (char === "\"") {
      inString = true;
      continue;
    }
    if (char === "'") {
      inChar = true;
      continue;
    }
    if (char === "{") depth += 1;
    if (char === "}") {
      depth -= 1;
      if (depth === 0) return index;
    }
  }
  return -1;
}

function extractJavaMethodSource(source, methodName) {
  if (!methodName) return "";
  const declaration = new RegExp(`(?:public|protected|private)\\s+[^;{}=]*\\b${methodName}\\s*\\(`);
  const match = declaration.exec(source);
  if (!match) return "";
  const openBrace = source.indexOf("{", match.index);
  if (openBrace < 0) return "";
  const closeBrace = findMatchingBrace(source, openBrace);
  if (closeBrace < 0) return "";
  const start = source.lastIndexOf("\n", match.index) + 1;
  return source.slice(start, closeBrace + 1).trim();
}

async function extractFailingTestSource(workspaceRepo, failingTestIdentifier) {
  const { className, methodName } = testIdentifierParts(failingTestIdentifier);
  if (!className || !methodName) return "";
  const relativeClassPath = `${className.replaceAll(".", "/")}.java`;
  const candidates = [
    `tests/${relativeClassPath}`,
    `test/${relativeClassPath}`,
    `src/test/java/${relativeClassPath}`,
  ];
  for (const candidate of candidates) {
    const abs = path.join(workspaceRepo, candidate);
    if (!fsSync.existsSync(abs)) continue;
    const source = await fs.readFile(abs, "utf8");
    const methodSource = extractJavaMethodSource(source, methodName);
    if (methodSource) return methodSource;
  }
  return "";
}

function yamlScalar(value) {
  return JSON.stringify(String(value ?? ""));
}

function yamlBlock(value, indent = 4) {
  const prefix = " ".repeat(indent);
  return String(value ?? "")
    .split(/\r?\n/)
    .map((line) => `${prefix}${line}`)
    .join("\n");
}

function boundedSeconds(value, fallback, { min = 0, max = 7200 } = {}) {
  const numeric = Number(value);
  const seconds = Number.isFinite(numeric) ? numeric : fallback;
  return Math.max(min, Math.min(max, seconds));
}

export function miniSweRuntimeModelName(agent, providerConfig = null) {
  const provider = String(providerConfig?.provider ?? agent?.provider ?? "").trim().toLowerCase();
  const model = String(providerConfig?.model ?? agent?.model ?? "").trim();
  if (provider === "openai" && model && !model.includes("/")) return `openai/${model}`;
  return model;
}

function buildMiniSweProcessEnvironment({ agent, providerConfig, env, runDir }) {
  const runtimeModel = miniSweRuntimeModelName(agent, providerConfig);
  const providerEnv = buildProviderEnvironment(agent, env).env;
  const pythonPath = [adapterModuleDir, providerEnv.PYTHONPATH].filter(Boolean).join(path.delimiter);
  return {
    env: {
      ...providerEnv,
      MSWEA_CONFIGURED: "true",
      MSWEA_GLOBAL_CONFIG_DIR: path.join(runDir, ".mini-swe-agent"),
      MSWEA_MODEL_NAME: runtimeModel,
      MSWEA_SILENT_STARTUP: "1",
      PYTHONPATH: pythonPath,
    },
    runtimeModel,
  };
}

function rankingPayloadFromSubmission(submission) {
  const predictions = Array.isArray(submission?.predictions)
    ? submission.predictions.map((prediction, index) => ({
        rank: Number(prediction.rank ?? index + 1),
        class: String(prediction.class ?? ""),
        method: String(prediction.method ?? ""),
      }))
    : [];
  return { predictions };
}

function latestInvalidSubmission(trajectory) {
  const messages = Array.isArray(trajectory?.messages) ? trajectory.messages : [];
  for (const message of [...messages].reverse()) {
    const submission = message?.extra?.fault_localization_submission;
    if (submission && submission.ok === false) return submission;
  }
  return null;
}

function miniSweExitStatus(trajectory) {
  const status = trajectory?.info?.exit_status;
  if (typeof status === "string" && status) return status;
  const messages = Array.isArray(trajectory?.messages) ? trajectory.messages : [];
  const exit = [...messages].reverse().find((message) => message?.role === "exit");
  return typeof exit?.extra?.exit_status === "string" ? exit.extra.exit_status : "";
}

function classifyMiniSweFailure({ processResult, rawOutput, miniTrajectory, structuredSubmission }) {
  if (processResult.timed_out) return "timeout";
  if (structuredSubmission?.ok) return "completed";
  const exitStatus = miniSweExitStatus(miniTrajectory);
  if (
    /AuthenticationError|PermissionDeniedError|RateLimitError|InternalServerError|OpenAIException|litellm\./i.test(rawOutput) ||
    /AuthenticationError|PermissionDeniedError|RateLimitError|InternalServerError|OpenAIException/i.test(exitStatus)
  ) {
    return "provider_error";
  }
  if (/RepeatedFormatError|FormatError|No tool calls found|Unknown tool/i.test(`${exitStatus}\n${rawOutput}`)) {
    return "agent_protocol_error";
  }
  if (latestInvalidSubmission(miniTrajectory) || miniTrajectory?.info?.submission) return "invalid_ranking";
  return processResult.exit_code === 0 ? "invalid_ranking" : "agent_protocol_error";
}

function miniSweStatusReason({ status, executionTimeoutSeconds, miniTrajectory }) {
  if (status === "completed") {
    return "mini-swe-agent submitted a schema-valid fault-localization ranking.";
  }
  if (status === "timeout") {
    return `mini-swe-agent exceeded the ${executionTimeoutSeconds}-second benchmark execution timeout; raw output and partial artifacts were preserved.`;
  }
  if (status === "provider_error") {
    return "mini-swe-agent reached the model provider but the provider call failed; raw output and partial artifacts were preserved.";
  }
  if (status === "agent_protocol_error") {
    return "mini-swe-agent violated its tool-call protocol before a valid fault-localization submission was recorded.";
  }
  const invalid = latestInvalidSubmission(miniTrajectory);
  if (invalid?.errors?.length) {
    return `Fault-localization submission was invalid: ${invalid.errors.map((error) => error.message ?? error.code).join("; ")}`;
  }
  return "mini-swe-agent did not submit exactly 10 valid production Class::method predictions.";
}

async function runWithTimeout(fn, timeoutMs, label) {
  let timer = null;
  try {
    return await Promise.race([
      fn(),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(`${label} exceeded ${timeoutMs}ms`)), timeoutMs);
      }),
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

async function writeMiniConfig({
  runDir,
  workspaceRepo,
  runtimeModel,
  budget,
  renderedPrompt,
  trajectoryPath,
  methodCatalogPath,
  submissionPath,
}) {
  const configPath = path.join(runDir, "mini-swe-agent.config.yaml");
  const executionTimeoutSeconds = boundedSeconds(
    budget.timeout_seconds,
    DEFAULT_BENCHMARK_EXECUTION_TIMEOUT_SECONDS,
    { min: 0, max: 7200 },
  );
  const config = `run:
  task: |
${yamlBlock(renderedPrompt, 4)}
agent:
  agent_class: default
  system_template: |
    You are a careful benchmark participant. Follow the task instructions exactly and do not edit repository files.
    Every assistant response must contain at least one tool call.
    Use bash only for investigation commands, and use submit_fault_localization to submit the final ranking.
  instance_template: |
    {{task}}
  step_limit: ${Number(budget.max_tool_calls)}
  cost_limit: 0
  wall_time_limit_seconds: ${executionTimeoutSeconds}
  output_path: ${yamlScalar(trajectoryPath)}
  mode: yolo
environment:
  environment_class: "mini_swe_fault_localization.FaultLocalizationEnvironment"
  cwd: ${yamlScalar(workspaceRepo)}
  timeout: ${Math.max(30, Math.min(600, executionTimeoutSeconds))}
  method_catalog_path: ${yamlScalar(methodCatalogPath)}
  submission_output_path: ${yamlScalar(submissionPath)}
  env:
    PAGER: cat
    MANPAGER: cat
    LESS: "-R"
    PIP_PROGRESS_BAR: "off"
    TQDM_DISABLE: "1"
model:
  model_class: "mini_swe_fault_localization.FaultLocalizationModel"
  model_name: ${yamlScalar(runtimeModel)}
  model_kwargs:
    drop_params: true
`;
  await fs.writeFile(configPath, config);
  return configPath;
}

async function writeMethodCatalog(runDir, entries) {
  const catalogPath = path.join(runDir, "method_catalog.json");
  await fs.writeFile(
    catalogPath,
    `${JSON.stringify(
      {
        schema_version: "d4j-method-catalog/v1",
        source: "agent-visible buggy repository",
        methods: entries,
        generated_at: new Date().toISOString(),
      },
      null,
      2,
    )}\n`,
  );
  return catalogPath;
}

async function readJsonIfExists(filePath) {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch {
    return null;
  }
}

async function redactFileKnownSecrets(filePath, env) {
  try {
    const text = await fs.readFile(filePath, "utf8");
    const redacted = redactKnownSecrets(text, env);
    if (redacted !== text) await fs.writeFile(filePath, redacted);
  } catch {
    // Optional mini-swe-agent artifacts may not exist if startup fails early.
  }
}

async function applyPatch(workspaceRepo, patchPath) {
  if (!fsSync.existsSync(patchPath)) {
    return {
      patch: path.basename(patchPath),
      status: "missing",
      exit_code: null,
      stdout: "",
      stderr: "",
    };
  }
  const dryRun = await runProcess("patch", ["-p1", "--forward", "--batch", "--dry-run", "-i", patchPath], {
    cwd: workspaceRepo,
    timeout: 60000,
  });
  if (dryRun.exit_code !== 0) {
    return {
      patch: path.basename(patchPath),
      status: "failed",
      exit_code: dryRun.exit_code,
      stdout: dryRun.stdout,
      stderr: dryRun.stderr || dryRun.error,
    };
  }
  const result = await runProcess("patch", ["-p1", "--forward", "--batch", "-i", patchPath], {
    cwd: workspaceRepo,
    timeout: 60000,
  });
  return {
    patch: path.basename(patchPath),
    status: result.exit_code === 0 ? "applied" : "failed",
    exit_code: result.exit_code,
    stdout: result.stdout,
    stderr: result.stderr || result.error,
  };
}

async function applyChartSecondaryFallback(workspaceRepo) {
  const sourceFile = safeResolveWithin(
    workspaceRepo,
    "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
  );
  const testFile = safeResolveWithin(
    workspaceRepo,
    "tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java",
  );
  const sourceText = await fs.readFile(sourceFile, "utf8");
  if (sourceText.includes("CategoryDataset dataset = p.getDataset(datasetIndex);")) {
    await fs.writeFile(
      sourceFile,
      sourceText.replace("CategoryDataset dataset = p.getDataset(datasetIndex);", "CategoryDataset dataset = p.getDataset();"),
    );
  }

  const testText = await fs.readFile(testFile, "utf8");
  if (!testText.includes("testLegendItemsForSecondaryDataset")) {
    const insertion = `    /**
     * A renderer assigned to a secondary dataset should build legend items
     * from that secondary dataset rather than the plot's primary dataset.
     */
    public void testLegendItemsForSecondaryDataset() {
        DefaultCategoryDataset primary = new DefaultCategoryDataset();
        primary.addValue(1.0, "Primary", "C1");
        DefaultCategoryDataset secondary = new DefaultCategoryDataset();
        secondary.addValue(2.0, "Secondary", "C1");

        AbstractCategoryItemRenderer r = new LevelRenderer();
        CategoryPlot plot = new CategoryPlot();
        plot.setDataset(primary);
        plot.setDataset(1, secondary);
        plot.setRenderer(1, r);

        LegendItemCollection lic = r.getLegendItems();
        assertEquals(1, lic.getItemCount());
        assertEquals("Secondary", lic.get(0).getLabel());
    }

`;
    const marker = "    /**\n     * A test that reproduces the problem reported in bug 2947660.";
    if (!testText.includes(marker)) {
      throw new Error("Could not find insertion point for Chart secondary trigger test");
    }
    const withImport = testText.includes("import org.jfree.chart.renderer.category.LevelRenderer;")
      ? testText
      : testText.replace(
          "import org.jfree.chart.renderer.category.CategoryItemRenderer;\n",
          "import org.jfree.chart.renderer.category.CategoryItemRenderer;\nimport org.jfree.chart.renderer.category.LevelRenderer;\n",
        );
    await fs.writeFile(testFile, withImport.replace(marker, `${insertion}${marker}`));
  }
  return {
    status: "applied",
    strategy: "chart-secondary-known-evidence-fallback",
    changed_files: [
      "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
      "tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java",
    ],
  };
}

async function verifyChartSecondarySourceState(workspaceRepo) {
  const sourceFile = safeResolveWithin(
    workspaceRepo,
    "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
  );
  const testFile = safeResolveWithin(
    workspaceRepo,
    "tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java",
  );
  const sourceText = await fs.readFile(sourceFile, "utf8");
  const testText = await fs.readFile(testFile, "utf8");
  const triggerSource = extractJavaMethodSource(testText, "testLegendItemsForSecondaryDataset");
  const verification = {
    status: "pass",
    checks: {
      intended_production_fault_present: sourceText.includes("CategoryDataset dataset = p.getDataset();"),
      validated_level_renderer_trigger_present: triggerSource.includes("new LevelRenderer()"),
      stale_line_and_shape_trigger_absent: !triggerSource.includes("new LineAndShapeRenderer()"),
    },
  };
  const failed = Object.entries(verification.checks)
    .filter(([, ok]) => !ok)
    .map(([name]) => name);
  if (failed.length > 0) {
    verification.status = "fail";
    verification.failed_checks = failed;
    throw new Error(`Variant workspace source-state verification failed: ${failed.join(", ")}`);
  }
  return verification;
}

function extractSubmissionFromTrajectory(trajectory) {
  const submission = trajectory?.info?.submission;
  if (typeof submission === "string" && submission.trim()) return submission;
  const messages = Array.isArray(trajectory?.messages) ? trajectory.messages : [];
  const exit = [...messages].reverse().find((message) => message?.role === "exit");
  if (typeof exit?.extra?.submission === "string" && exit.extra.submission.trim()) return exit.extra.submission;
  if (typeof exit?.content === "string" && exit.content.trim()) return exit.content;
  return "";
}

export class MiniSweAgentAdapter extends AgentAdapter {
  constructor({ repoRoot, checkoutRoot, variantsRoot, env = process.env } = {}) {
    super();
    this.repoRoot = repoRoot ?? process.cwd();
    this.checkoutRoot = checkoutRoot ?? path.join(this.repoRoot, "workspaces", "defects4j");
    this.variantsRoot = variantsRoot ?? path.join(this.repoRoot, "new_bug_variants");
    this.env = env;
  }

  async inspectAvailability(env = this.env) {
    const override = env.MINI_SWE_AGENT_BIN;
    const candidates = [];
    if (override) candidates.push({ path: override, source: "MINI_SWE_AGENT_BIN" });
    const miniSweAgent = await commandPath("mini-swe-agent");
    if (miniSweAgent) candidates.push({ path: miniSweAgent, source: "PATH:mini-swe-agent" });
    const mini = await commandPath("mini");
    if (mini) candidates.push({ path: mini, source: "PATH:mini" });

    const found = candidates.find((candidate) => fsSync.existsSync(candidate.path));
    if (!found) {
      return {
        framework: "mini-swe-agent",
        available: false,
        path: "",
        source: "missing",
        version: "",
        supported_invocation:
          "mini-swe-agent --config <run-config.yaml> --model <model> --yolo --output <trajectory.json> --exit-immediately",
        trajectory_format: "mini-swe-agent-1.1 JSON trajectory",
        install_requirement: installRequirement,
      };
    }

    const versionResult = await runProcess(found.path, ["--version"], { timeout: 10000 });
    const helpResult = versionResult.exit_code === 0 ? null : await runProcess(found.path, ["--help"], { timeout: 10000 });
    return {
      framework: "mini-swe-agent",
      available: true,
      path: found.path,
      source: found.source,
      version: (versionResult.stdout || versionResult.stderr || helpResult?.stdout || "").trim().split(/\r?\n/)[0],
      supported_invocation:
        "mini-swe-agent --config <run-config.yaml> --model <model> --yolo --output <trajectory.json> --exit-immediately",
      trajectory_format: "mini-swe-agent-1.1 JSON trajectory",
      install_requirement: installRequirement,
    };
  }

  async prepareRun({ runDir, taskBundle }) {
    const workspaceRoot = path.join(runDir, "workspace");
    const workspaceRepo = path.join(workspaceRoot, workspaceLabelForTask(taskBundle));
    const stagingRoot = path.join(runDir, "staging");
    const stagingRepo = path.join(stagingRoot, workspaceLabelForTask(taskBundle));
    await fs.rm(workspaceRoot, { recursive: true, force: true });
    await fs.rm(stagingRoot, { recursive: true, force: true });
    await fs.mkdir(workspaceRoot, { recursive: true });
    await fs.mkdir(stagingRoot, { recursive: true });

    const project = taskBundle.source.project;
    const bugId = taskBundle.source.bug_id;
    const sourceCheckout =
      taskBundle.task_type === "original"
        ? path.join(this.checkoutRoot, `${project}-${bugId}`, "buggy")
        : path.join(this.checkoutRoot, `${project}-${bugId}`, "fixed");

    if (!fsSync.existsSync(sourceCheckout)) {
      throw new Error(`Required checkout is missing: ${path.relative(this.repoRoot, sourceCheckout)}`);
    }

    await copyDirectoryFiltered(sourceCheckout, stagingRepo);
    await stripHistoryDirs(stagingRepo);

    const patch_results = [];
    let variantFallback = null;
    let sourceStateVerification = null;
    if (taskBundle.task_type === "variant") {
      const variantDir = assertInside(
        this.variantsRoot,
        taskBundle.private_adapter?.variant_dir ?? "",
        "Variant artifact directory",
      );
      const variantPatch = assertInside(variantDir, path.join(variantDir, "variant.patch"), "Variant patch");
      const testPatch = assertInside(variantDir, path.join(variantDir, "test.patch"), "Variant test patch");
      patch_results.push(await applyPatch(stagingRepo, variantPatch));
      patch_results.push(await applyPatch(stagingRepo, testPatch));
      if (patch_results.some((result) => result.status !== "applied")) {
        if (taskBundle.task_id === CHART_SECONDARY_VARIANT_ID) {
          variantFallback = await applyChartSecondaryFallback(stagingRepo);
        } else {
          throw new Error(`Could not apply variant patches for ${taskBundle.task_id}`);
        }
      }
      if (taskBundle.task_id === CHART_SECONDARY_VARIANT_ID) {
        sourceStateVerification = await verifyChartSecondarySourceState(stagingRepo);
      }
    }

    const stagingSanitization = await sanitizeAgentWorkspace(stagingRepo);
    await copyDirectoryFiltered(stagingRepo, workspaceRepo);
    const finalSanitization = await sanitizeAgentWorkspace(workspaceRepo);
    await fs.rm(stagingRoot, { recursive: true, force: true });

    const scan = await scanPrivateMetadata(workspaceRepo);
    const sourceHashes = await hashSourceFiles(workspaceRepo);
    const methodCatalogEntries = await buildJavaMethodCatalogEntries(workspaceRepo);
    const methodCatalog = new Set(methodCatalogEntries.map((entry) => entry.qualified));
    const methodCatalogPath = await writeMethodCatalog(runDir, methodCatalogEntries);
    const failingTestSource =
      taskBundle.agent_visible_task.failing_test_source ||
      (await extractFailingTestSource(workspaceRepo, taskBundle.agent_visible_task.failing_test_identifier));
    const agentVisibleTask = {
      ...taskBundle.agent_visible_task,
      failing_test_source: failingTestSource,
      read_only_buggy_repository_path: workspaceRepo,
    };
    const workspaceManifest = {
      schema_version: "d4j-agent-workspace/v1",
      task_id: taskBundle.task_id,
      task_type: taskBundle.task_type,
      workspace_label: workspaceLabelForTask(taskBundle),
      workspace_root: path.relative(this.repoRoot, workspaceRoot),
      agent_visible_repository_path: workspaceRepo,
      source_checkout: path.relative(this.repoRoot, sourceCheckout),
      copied_only_task_checkout: true,
      patch_staging_root: path.relative(this.repoRoot, stagingRoot),
      patch_staging_removed: !fsSync.existsSync(stagingRoot),
      git_history_stripped: !scan.git_history_leak,
      private_metadata_scan: scan,
      staging_sanitization: stagingSanitization,
      final_sanitization: finalSanitization,
      variant_patch_results: patch_results,
      variant_fallback: variantFallback,
      source_state_verification: sourceStateVerification,
      method_catalog_size: methodCatalog.size,
      method_catalog_path: path.relative(this.repoRoot, methodCatalogPath),
      source_hash_file_count: sourceHashes.file_count,
      prepared_at: new Date().toISOString(),
    };

    await fs.writeFile(path.join(runDir, "workspace_manifest.json"), `${JSON.stringify(workspaceManifest, null, 2)}\n`);
    await fs.writeFile(path.join(runDir, "source_hashes_before.json"), `${JSON.stringify(sourceHashes, null, 2)}\n`);

    return {
      workspace_root: workspaceRoot,
      workspace_repo: workspaceRepo,
      agent_visible_task: agentVisibleTask,
      workspace_manifest: workspaceManifest,
      source_hashes_before: sourceHashes,
      method_catalog: methodCatalog,
      method_catalog_path: methodCatalogPath,
      isolation: {
        fixed_code_inaccessible: taskBundle.task_type === "original" ? workspaceLabelForTask(taskBundle).endsWith("b") : true,
        git_history_inaccessible: !scan.git_history_leak,
        patch_backups_inaccessible: !scan.patch_backup_leak,
        private_metadata_inaccessible: !scan.private_benchmark_metadata_leak,
        fixed_revision_inaccessible: !scan.fixed_revision_leak,
        unexpected_artifacts_inaccessible: !scan.unexpected_artifact_leak,
        workspace_isolation_ok: scan.ok,
        scan,
      },
    };
  }

  async execute({ runDir, agent, budget, prepared, renderedPrompt }) {
    const startupTimeoutMs = MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS * 1000;
    let providerConfig = null;
    let availability = null;
    try {
      ({ providerConfig, availability } = await runWithTimeout(
        async () => ({
          providerConfig: resolveProviderConfig(agent, this.env),
          availability: await this.inspectAvailability(this.env),
        }),
        startupTimeoutMs,
        "mini-swe-agent provider initialization",
      ));
    } catch (error) {
      const statusReason = error instanceof Error ? error.message : "mini-swe-agent provider initialization timed out";
      return {
        status: "startup_timeout",
        status_reason: statusReason,
        provider_config: providerConfig,
        adapter: availability,
        raw_output: "",
        commands: `startup_timeout_seconds: ${MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS}\nstartup_error: ${statusReason}\n`,
        trajectory: [],
        test_runs: [],
        ranking_text: "",
        timeouts: {
          agent_startup_seconds: MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS,
          benchmark_execution_seconds: boundedSeconds(
            budget.timeout_seconds,
            DEFAULT_BENCHMARK_EXECUTION_TIMEOUT_SECONDS,
            { min: 30, max: 7200 },
          ),
          execution_timer_starts: "after mini-swe-agent process launch for the fault-localization task",
        },
      };
    }
    if (!providerConfig.configured) {
      return {
        status: "provider_not_configured",
        status_reason: providerConfig.message,
        provider_config: providerConfig,
        adapter: availability,
        raw_output: "",
        commands: "",
        trajectory: [],
        test_runs: [],
        ranking_text: "",
        timeouts: {
          agent_startup_seconds: MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS,
          benchmark_execution_seconds: boundedSeconds(
            budget.timeout_seconds,
            DEFAULT_BENCHMARK_EXECUTION_TIMEOUT_SECONDS,
            { min: 30, max: 7200 },
          ),
          execution_timer_starts: "after mini-swe-agent process launch for the fault-localization task",
        },
      };
    }
    if (!availability.available) {
      return {
        status: "agent_not_installed",
        status_reason: `mini-swe-agent is not installed. Install with: ${installRequirement}`,
        provider_config: providerConfig,
        adapter: availability,
        raw_output: "",
        commands: "",
        trajectory: [],
        test_runs: [],
        ranking_text: "",
        timeouts: {
          agent_startup_seconds: MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS,
          benchmark_execution_seconds: boundedSeconds(
            budget.timeout_seconds,
            DEFAULT_BENCHMARK_EXECUTION_TIMEOUT_SECONDS,
            { min: 30, max: 7200 },
          ),
          execution_timer_starts: "after mini-swe-agent process launch for the fault-localization task",
        },
      };
    }

    const trajectoryPath = path.join(runDir, "mini-swe-agent.traj.json");
    const submissionPath = path.join(runDir, "fault-localization-submission.json");
    const executionTimeoutSeconds = boundedSeconds(
      budget.timeout_seconds,
      DEFAULT_BENCHMARK_EXECUTION_TIMEOUT_SECONDS,
      { min: 0, max: 7200 },
    );
    const { env: providerEnv, runtimeModel } = buildMiniSweProcessEnvironment({
      agent,
      providerConfig,
      env: this.env,
      runDir,
    });
    await fs.mkdir(providerEnv.MSWEA_GLOBAL_CONFIG_DIR, { recursive: true });
    const configPath = await writeMiniConfig({
      runDir,
      workspaceRepo: prepared.workspace_repo,
      runtimeModel,
      budget,
      renderedPrompt,
      trajectoryPath,
      methodCatalogPath: prepared.method_catalog_path,
      submissionPath,
    });
    const args = [
      "--config",
      configPath,
      "--model",
      runtimeModel,
      "--yolo",
      "--output",
      trajectoryPath,
      "--exit-immediately",
    ];
    const result = await runProcess(availability.path, args, {
      cwd: prepared.workspace_repo,
      env: providerEnv,
      timeout: executionTimeoutSeconds * 1000,
      killSignal: "SIGTERM",
      maxBuffer: 50 * 1024 * 1024,
    });
    await redactFileKnownSecrets(trajectoryPath, providerEnv);
    const trajectory = await this.collectTrajectory({ trajectoryPath, prepared });
    const miniTrajectory = await readJsonIfExists(trajectoryPath);
    const structuredSubmission = await readJsonIfExists(submissionPath);
    const rawOutput = redactKnownSecrets(`${result.stdout}${result.stderr ? `\n${result.stderr}` : ""}`, providerEnv);
    const status = classifyMiniSweFailure({
      processResult: result,
      rawOutput,
      miniTrajectory,
      structuredSubmission,
    });
    const rankingPayload = status === "completed" ? rankingPayloadFromSubmission(structuredSubmission) : null;
    const rankingText =
      status === "completed"
        ? rankingPayload.predictions.map((prediction) => `${prediction.rank}. ${prediction.class}::${prediction.method}`).join("\n")
        : "";
    const commandText = [
      `$ ${path.basename(availability.path)} --config ${path.basename(configPath)} --model ${runtimeModel} --yolo --output ${path.basename(
        trajectoryPath,
      )} --exit-immediately`,
      `cwd: ${prepared.workspace_repo}`,
      `startup_timeout_seconds: ${MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS}`,
      `execution_timeout_seconds: ${executionTimeoutSeconds}`,
      `execution_timer_started_at: ${result.started_at}`,
      `exit_code: ${result.exit_code}`,
      `signal: ${result.signal ?? ""}`,
      `timed_out: ${result.timed_out}`,
      `duration_ms: ${result.duration_ms}`,
    ].join("\n");

    return {
      status,
      status_reason: miniSweStatusReason({ status, executionTimeoutSeconds, miniTrajectory }),
      provider_config: providerConfig,
      adapter: { ...availability, runtime_model: runtimeModel },
      raw_output: rawOutput,
      commands: `${commandText}\n`,
      trajectory,
      test_runs: trajectory
        .filter((event) => event.type === "test_run")
        .map((event, index) => ({
          test_id: prepared.agent_visible_task.failing_test_identifier || event.target,
          run_number: index + 1,
          status: "recorded",
          output: event.target,
        })),
      ranking_text: rankingText,
      ranking_payload: rankingPayload,
      structured_submission: structuredSubmission ?? null,
      timeouts: {
        agent_startup_seconds: MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS,
        benchmark_execution_seconds: executionTimeoutSeconds,
        execution_timer_starts: "after mini-swe-agent process launch for the fault-localization task",
      },
    };
  }

  async smokeTest({ runDir, agent, executionTimeoutSeconds = DEFAULT_BENCHMARK_EXECUTION_TIMEOUT_SECONDS } = {}) {
    await fs.mkdir(runDir, { recursive: true });
    const workspaceRepo = path.join(runDir, "workspace");
    await fs.mkdir(workspaceRepo, { recursive: true });
    await fs.writeFile(path.join(workspaceRepo, "README.md"), "D4J Variant Lab mini-swe-agent smoke workspace.\n");
    await fs.mkdir(path.join(workspaceRepo, "source", "org", "example"), { recursive: true });
    await fs.writeFile(
      path.join(workspaceRepo, "source", "org", "example", "Smoke.java"),
      `package org.example;

public class Smoke {
    public void m0() {}
    public void m1() {}
    public void m2() {}
    public void m3() {}
    public void m4() {}
    public void m5() {}
    public void m6() {}
    public void m7() {}
    public void m8() {}
    public void m9() {}
}
`,
    );

    const startupTimeoutMs = MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS * 1000;
    let providerConfig = null;
    let availability = null;
    try {
      ({ providerConfig, availability } = await runWithTimeout(
        async () => ({
          providerConfig: resolveProviderConfig(agent, this.env),
          availability: await this.inspectAvailability(this.env),
        }),
        startupTimeoutMs,
        "mini-swe-agent provider initialization",
      ));
    } catch (error) {
      const statusReason = error instanceof Error ? error.message : "mini-swe-agent provider initialization timed out";
      const result = {
        status: "startup_timeout",
        status_reason: statusReason,
        provider_config: providerConfig,
        adapter: availability,
        raw_output: "",
        commands: `startup_timeout_seconds: ${MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS}\nstartup_error: ${statusReason}\n`,
        timeouts: {
          agent_startup_seconds: MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS,
          benchmark_execution_seconds: executionTimeoutSeconds,
          execution_timer_starts: "after mini-swe-agent process launch for the smoke task",
        },
      };
      await fs.writeFile(path.join(runDir, "smoke_result.json"), `${JSON.stringify(result, null, 2)}\n`);
      return result;
    }

    if (!providerConfig.configured || !availability.available) {
      const result = {
        status: providerConfig.configured ? "agent_not_installed" : "provider_not_configured",
        status_reason: providerConfig.configured
          ? `mini-swe-agent is not installed. Install with: ${installRequirement}`
          : providerConfig.message,
        provider_config: providerConfig,
        adapter: availability,
        raw_output: "",
        commands: "",
        timeouts: {
          agent_startup_seconds: MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS,
          benchmark_execution_seconds: executionTimeoutSeconds,
          execution_timer_starts: "after mini-swe-agent process launch for the smoke task",
        },
      };
      await fs.writeFile(path.join(runDir, "smoke_result.json"), `${JSON.stringify(result, null, 2)}\n`);
      return result;
    }

    const safeExecutionTimeoutSeconds = boundedSeconds(
      executionTimeoutSeconds,
      DEFAULT_BENCHMARK_EXECUTION_TIMEOUT_SECONDS,
      { min: 30, max: 7200 },
    );
    const trajectoryPath = path.join(runDir, "mini-swe-agent-smoke.traj.json");
    const submissionPath = path.join(runDir, "fault-localization-submission.json");
    const methodCatalogPath = await writeMethodCatalog(runDir, await buildJavaMethodCatalogEntries(workspaceRepo));
    const { env: providerEnv, runtimeModel } = buildMiniSweProcessEnvironment({
      agent,
      providerConfig,
      env: this.env,
      runDir,
    });
    await fs.mkdir(providerEnv.MSWEA_GLOBAL_CONFIG_DIR, { recursive: true });
    const configPath = await writeMiniConfig({
      runDir,
      workspaceRepo,
      runtimeModel,
      budget: { max_tool_calls: 3, max_test_runs: 1, timeout_seconds: safeExecutionTimeoutSeconds },
      renderedPrompt:
        'This is a non-interactive smoke test for the fault-localization submission tool. Do not call bash. Call submit_fault_localization exactly once with predictions org.example.Smoke::m0 through org.example.Smoke::m9 in order.',
      trajectoryPath,
      methodCatalogPath,
      submissionPath,
    });
    const args = [
      "--config",
      configPath,
      "--model",
      runtimeModel,
      "--yolo",
      "--output",
      trajectoryPath,
      "--exit-immediately",
    ];
    const processResult = await runProcess(availability.path, args, {
      cwd: workspaceRepo,
      env: providerEnv,
      timeout: safeExecutionTimeoutSeconds * 1000,
      killSignal: "SIGTERM",
      maxBuffer: 20 * 1024 * 1024,
    });
    await redactFileKnownSecrets(trajectoryPath, providerEnv);
    const rawOutput = redactKnownSecrets(
      `${processResult.stdout}${processResult.stderr ? `\n${processResult.stderr}` : ""}`,
      providerEnv,
    );
    const miniTrajectory = await readJsonIfExists(trajectoryPath);
    const structuredSubmission = await readJsonIfExists(submissionPath);
    const submission = extractSubmissionFromTrajectory(miniTrajectory);
    const sawInteractivePrompt =
      /Enter your default model|What do you want to do|To get started, we need to set up your global config file/i.test(rawOutput);
    const passed =
      processResult.exit_code === 0 &&
      !sawInteractivePrompt &&
      structuredSubmission?.ok === true &&
      structuredSubmission.predictions?.length === 10;
    const status = processResult.timed_out ? "timeout" : passed ? "passed" : "failed";
    const commandText = [
      `$ ${path.basename(availability.path)} --config ${path.basename(configPath)} --model ${runtimeModel} --yolo --output ${path.basename(
        trajectoryPath,
      )} --exit-immediately`,
      `cwd: ${workspaceRepo}`,
      `startup_timeout_seconds: ${MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS}`,
      `execution_timeout_seconds: ${safeExecutionTimeoutSeconds}`,
      `execution_timer_started_at: ${processResult.started_at}`,
      `exit_code: ${processResult.exit_code}`,
      `signal: ${processResult.signal ?? ""}`,
      `timed_out: ${processResult.timed_out}`,
      `duration_ms: ${processResult.duration_ms}`,
      `interactive_prompt_detected: ${sawInteractivePrompt}`,
    ].join("\n");
    const result = {
      status,
      status_reason:
        status === "passed"
          ? "mini-swe-agent started non-interactively with the configured provider and submitted a schema-valid fault-localization ranking."
          : status === "timeout"
            ? `mini-swe-agent smoke exceeded the ${safeExecutionTimeoutSeconds}-second execution timeout.`
            : "mini-swe-agent smoke did not submit the expected structured ranking; raw output was preserved.",
      provider_config: providerConfig,
      adapter: { ...availability, runtime_model: runtimeModel },
      raw_output: rawOutput,
      commands: `${commandText}\n`,
      submission,
      structured_submission: structuredSubmission ?? null,
      trajectory_path: trajectoryPath,
      timeouts: {
        agent_startup_seconds: MINI_SWE_AGENT_STARTUP_TIMEOUT_SECONDS,
        benchmark_execution_seconds: safeExecutionTimeoutSeconds,
        execution_timer_starts: "after mini-swe-agent process launch for the smoke task",
      },
    };
    await fs.writeFile(path.join(runDir, "commands.log"), result.commands);
    await fs.writeFile(path.join(runDir, "raw_agent_output.txt"), result.raw_output);
    await fs.writeFile(path.join(runDir, "smoke_result.json"), `${JSON.stringify(result, null, 2)}\n`);
    return result;
  }

  parseResult({ raw_output, mini_trajectory }) {
    const submitted = extractSubmissionFromTrajectory(mini_trajectory);
    if (submitted) return submitted;
    const marker = "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT";
    const markerIndex = String(raw_output ?? "").lastIndexOf(marker);
    if (markerIndex >= 0) return String(raw_output).slice(markerIndex + marker.length).trim();
    return String(raw_output ?? "");
  }

  async collectTrajectory({ trajectoryPath, prepared }) {
    const raw = await readJsonIfExists(trajectoryPath);
    return normalizeTrajectoryEvents(raw, prepared.workspace_repo);
  }

  async collectSourceIntegrity(prepared) {
    const after = await hashSourceFiles(prepared.workspace_repo);
    const comparison = compareSourceHashes(prepared.source_hashes_before, after);
    return { after, comparison };
  }

  async writeTrajectory(runDir, events) {
    await fs.writeFile(path.join(runDir, "trajectory.jsonl"), trajectoryJsonl(events));
  }
}
