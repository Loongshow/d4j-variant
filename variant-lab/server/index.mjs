import express from "express";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  benchmarkProtocol,
  buildChartDepthLadder,
  buildOriginalAgentTask,
  buildVariantAgentTask,
  compareAgentRuns,
  compareOriginalVariantRuns,
  createBenchmarkRun,
  discoverBenchmarkRunRecords,
  ensureAgentProfiles,
  findBenchmarkRunById,
  groupBenchmarkRuns,
  listAgentProfiles,
  matchingPairForRun,
  readBenchmarkArtifact,
  recordToRunSummary,
  parseBenchmarkDurationMs,
  sanitizeBenchmarkId,
  saveAgentProfile,
  summarizeBenchmarkRuns,
  assertNoCredentialFields,
  normalizeBudget,
  withAgentRuntimeStatus,
} from "./benchmarkStore.mjs";
import { MiniSweAgentAdapter } from "./agents/miniSweAgentAdapter.mjs";
import {
  DEFAULT_BATCH_ID,
  checkpointBatchEntry,
  ensureBatch,
  readBatch,
  writeBatchOutputs,
} from "./batchStore.mjs";
import { constructVariantAttempt } from "./variantConstruction.mjs";
import {
  accuracyMetricNames,
  buildAccuracyAnalysis,
  selectAccuracyMetric,
  writeAccuracyAnalysis,
} from "./accuracyStore.mjs";
import {
  buildFaultLocalizationTask,
  canonicalRecordToRun,
  createBatchReport,
  createIncompleteVariant,
  discoverVariantRecords,
  emptyFaultLocalizationResult,
  ensureChartSecondaryVariant,
  groupVariantRecords,
  hasCanonicalValidatedBugVariant,
  readFaultLocalizationRuns,
  readVariantRecord,
  sanitizeVariantId,
  safeArtifactPath,
  summarizeVariantRecords,
  validationGatePasses,
  variantArtifactConsistency,
  variantBenchmarkEligibility,
  variantRecordToDetail,
  writeFaultLocalizationRun,
} from "./variantLibrary.mjs";

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(appRoot, "..");
const workspaceRoot = path.join(repoRoot, "workspaces");
const checkoutRoot = path.join(workspaceRoot, "defects4j");
const runsRoot = path.join(repoRoot, "runs");
const variantsRoot = path.join(repoRoot, "new_bug_variants");
const benchmarkRoot = path.join(repoRoot, "benchmark_runs");
const port = Number(process.env.D4J_API_PORT ?? 8787);
const miniSweAgentAdapter = new MiniSweAgentAdapter({ repoRoot, checkoutRoot, variantsRoot, env: process.env });

const artifactPlan = [
  {
    stepId: "agent-1",
    title: "Agent 1: Original Bug Analyst",
    artifacts: ["agent1_report.md"],
  },
  {
    stepId: "agent-2",
    title: "Agent 2: Variant Designer",
    artifacts: ["candidates.md"],
  },
  {
    stepId: "agent-3",
    title: "Agent 3: Benchmark Reviewer",
    artifacts: ["review.md"],
  },
  {
    stepId: "agent-4",
    title: "Agent 4: Implementer",
    artifacts: ["patch.diff"],
  },
  {
    stepId: "agent-5",
    title: "Agent 5: Validator / Packager",
    artifacts: ["validation.log", "variant_report.md"],
  },
];

const artifactKinds = {
  "agent1_report.md": "report",
  "candidates.md": "candidates",
  "review.md": "review",
  "patch.diff": "patch",
  "validation.log": "log",
  "variant_report.md": "report",
};

const nodeForDimension = {
  "fault-site relocation": "F: Fault",
  "trigger-condition substitution": "C: Input Constraint",
  "propagation-path modification": "P: Propagation",
  "failure-mode modification": "O: Observable Failure",
  "API-path substitution": "R: Public API Expectation",
};

let commandLog = [];
let lastCommandError = "";
let multiFamilyBatchJob = {
  running: false,
  batch_id: null,
  current: null,
  started_at: null,
  updated_at: null,
  error: null,
};

const app = express();
app.use(express.json({ limit: "1mb" }));
app.use((_, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  next();
});

app.options("*", (_, res) => res.sendStatus(204));

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

async function ensureLayout() {
  await Promise.all([
    fs.mkdir(checkoutRoot, { recursive: true }),
    fs.mkdir(runsRoot, { recursive: true }),
    fs.mkdir(variantsRoot, { recursive: true }),
    fs.mkdir(benchmarkRoot, { recursive: true }),
  ]);
  await ensureChartSecondaryVariant({ variantsRoot, runsRoot });
  await ensureAgentProfiles(benchmarkRoot, process.env);
}

function trimOutput(value, limit = 4000) {
  if (!value) return "";
  return value.length > limit ? `${value.slice(0, limit)}\n... trimmed ...` : value;
}

function rememberCommand(entry) {
  commandLog = [entry, ...commandLog].slice(0, 30);
  if (entry.exitCode !== 0 && entry.exitCode !== 1) {
    lastCommandError = entry.stderr || entry.stdout || entry.error || `${entry.command} exited ${entry.exitCode}`;
  }
}

function runCommand(command, args, options = {}) {
  const started = Date.now();
  const cwd = options.cwd ?? repoRoot;
  const allowedExitCodes = options.allowedExitCodes ?? [0];
  return new Promise((resolve, reject) => {
    execFile(
      command,
      args,
      {
        cwd,
        env: options.env ?? process.env,
        timeout: options.timeout ?? 120000,
        maxBuffer: options.maxBuffer ?? 20 * 1024 * 1024,
      },
      (error, stdout = "", stderr = "") => {
        const exitCode = typeof error?.code === "number" ? error.code : 0;
        const entry = {
          command: [command, ...args].join(" "),
          cwd,
          exitCode,
          durationMs: Date.now() - started,
          stdout: trimOutput(stdout),
          stderr: trimOutput(stderr),
          error: error?.message ?? "",
          timestamp: new Date().toISOString(),
        };
        rememberCommand(entry);

        if (error && !allowedExitCodes.includes(exitCode)) {
          reject(new ApiError(500, trimOutput(stderr || error.message)));
          return;
        }
        resolve({ stdout, stderr, exitCode });
      },
    );
  });
}

function shell(command) {
  return new Promise((resolve) => {
    execFile("sh", ["-lc", command], { cwd: repoRoot, timeout: 10000 }, (error, stdout = "", stderr = "") => {
      resolve({ ok: !error, stdout: stdout.trim(), stderr: stderr.trim() });
    });
  });
}

async function detectExecutable(name, fallbackPath) {
  const fromPath = await shell(`command -v ${name}`);
  if (fromPath.ok && fromPath.stdout) {
    return { available: true, path: fromPath.stdout, source: "PATH" };
  }

  if (fallbackPath && fsSync.existsSync(fallbackPath)) {
    return { available: true, path: fallbackPath, source: "repo fallback" };
  }

  return { available: false, path: "", source: "missing" };
}

async function detectVersion(command, args, env = process.env) {
  if (!command) return "";
  const result = await new Promise((resolve) => {
    execFile(command, args, { cwd: repoRoot, env, timeout: 10000 }, (error, stdout = "", stderr = "") => {
      resolve({ ok: !error, stdout: stdout.trim(), stderr: stderr.trim() });
    });
  });
  return trimOutput(result.stdout || result.stderr, 800).split("\n")[0] ?? "";
}

function unique(values) {
  return Array.from(new Set(values.filter(Boolean)));
}

function javaCandidates() {
  const pathCandidates = (process.env.PATH ?? "")
    .split(path.delimiter)
    .filter(Boolean)
    .map((dir) => path.join(dir, "java"));
  return unique([
    process.env.JAVA_HOME ? path.join(process.env.JAVA_HOME, "bin", "java") : "",
    ...pathCandidates,
    path.join(process.env.HOME ?? "", ".homebrew", "opt", "openjdk@11", "bin", "java"),
    path.join(process.env.HOME ?? "", ".homebrew", "opt", "openjdk", "bin", "java"),
    "/opt/homebrew/opt/openjdk@11/bin/java",
    "/opt/homebrew/opt/openjdk/bin/java",
    "/usr/local/opt/openjdk@11/bin/java",
    "/usr/local/opt/openjdk/bin/java",
  ]).filter((candidate) => fsSync.existsSync(candidate));
}

async function detectJava() {
  for (const candidate of javaCandidates()) {
    const version = await detectVersion(candidate, ["-version"]);
    if (version && !/unable to locate|operation couldn/i.test(version)) {
      return {
        available: true,
        path: candidate,
        source: candidate === (await shell("command -v java")).stdout ? "PATH" : "fallback",
        version,
      };
    }
  }
  const fallback = await detectExecutable("java");
  return {
    ...fallback,
    version: fallback.available ? await detectVersion(fallback.path, ["-version"]) : "",
  };
}

function envWithJava(java) {
  if (!java?.available || !java.path) return process.env;
  const javaBin = path.dirname(java.path);
  const pathParts = (process.env.PATH ?? "").split(path.delimiter).filter((part) => part && part !== javaBin);
  const javaHome = path.resolve(javaBin, "..");
  return {
    ...process.env,
    JAVA_HOME: process.env.JAVA_HOME || javaHome,
    PATH: [javaBin, ...pathParts].join(path.delimiter),
  };
}

async function getEnvStatus() {
  await ensureLayout();
  const defects4j = await detectExecutable("defects4j", path.join(repoRoot, "framework", "bin", "defects4j"));
  const java = await detectJava();
  const perl = await detectExecutable("perl");
  const toolEnv = envWithJava(java);
  const miniSweAgent = await miniSweAgentAdapter.inspectAvailability(process.env);
  const agentProfiles = await listAgentProfiles(benchmarkRoot, process.env);
  const gptProfile =
    agentProfiles.find((profile) => profile.framework === "mini-swe-agent" && profile.provider === "openai") ??
    agentProfiles[0];
  const gptRuntime = withAgentRuntimeStatus(gptProfile, { env: process.env, adapter: miniSweAgent });

  return {
    checks: [
      {
        id: "mini-swe-agent",
        status: miniSweAgent.available ? "ready" : "missing",
        details: {
          available: miniSweAgent.available,
          version: miniSweAgent.version ?? "",
        },
      },
      {
        id: "openai-provider",
        status: gptRuntime.runtime.provider_ready ? "ready" : "not_configured",
        details: {
          adapter_available: gptRuntime.runtime.adapter_available,
          credential_configured: gptRuntime.runtime.credential_configured,
          credential_source: gptRuntime.runtime.credential_source,
          model_configured: gptRuntime.runtime.model_configured,
          model: gptRuntime.model,
          provider_ready: gptRuntime.runtime.provider_ready,
        },
      },
    ],
    defects4j: {
      ...defects4j,
      version: defects4j.available ? await detectVersion(defects4j.path, ["help"], toolEnv) : "",
    },
    java,
    perl: {
      ...perl,
      version: perl.available ? await detectVersion(perl.path, ["-v"]) : "",
    },
    mini_swe_agent: miniSweAgent,
    openai_provider: gptRuntime.provider_config,
    repoRoot,
    workspaceRoot,
    checkoutRoot,
    path: toolEnv.PATH ?? "",
    lastCommandError,
    recentCommands: commandLog,
  };
}

async function defects4jCommand() {
  const env = await getEnvStatus();
  if (!env.defects4j.available) {
    throw new ApiError(503, "Defects4J is not available from PATH or framework/bin/defects4j");
  }
  return env.defects4j.path;
}

async function runDefects4j(args, options = {}) {
  const env = await getEnvStatus();
  const command = env.defects4j.path;
  if (!env.defects4j.available) {
    throw new ApiError(503, "Defects4J is not available from PATH or framework/bin/defects4j");
  }
  return runCommand(command, args, { ...options, env: envWithJava(env.java) });
}

function sanitizeProject(value) {
  const project = String(value ?? "").trim();
  if (!/^[A-Za-z][A-Za-z0-9]*$/.test(project)) {
    throw new ApiError(400, "Invalid project id");
  }
  return project;
}

function sanitizeBugId(value) {
  const bugId = Number(value);
  if (!Number.isInteger(bugId) || bugId <= 0) {
    throw new ApiError(400, "Invalid bug id");
  }
  return String(bugId);
}

function sanitizeLevel(value) {
  const level = String(value ?? "").trim();
  if (level !== "L10" && level !== "L20" && level !== "L30" && level !== "L50") {
    throw new ApiError(400, "Invalid variant level");
  }
  return level;
}

function sanitizeVersion(value) {
  const version = String(value ?? "").trim();
  if (version !== "buggy" && version !== "fixed" && version !== "b" && version !== "f") {
    throw new ApiError(400, "Invalid checkout version");
  }
  return version === "b" || version === "buggy" ? "buggy" : "fixed";
}

function safeResolve(root, requestedPath = "") {
  const relativePath = String(requestedPath);
  if (!relativePath || path.isAbsolute(relativePath) || relativePath.includes("\0")) {
    throw new ApiError(400, "Invalid file path");
  }
  const target = path.resolve(root, relativePath);
  const rootWithSep = root.endsWith(path.sep) ? root : `${root}${path.sep}`;
  if (target !== root && !target.startsWith(rootWithSep)) {
    throw new ApiError(400, "Rejected path traversal attempt");
  }
  return target;
}

function bugSlug(project, bugId) {
  return `${project}-${bugId}`;
}

function checkoutPath(project, bugId, version) {
  return path.join(checkoutRoot, bugSlug(project, bugId), version);
}

function analysisDir(project, bugId) {
  return path.join(runsRoot, bugSlug(project, bugId), "analysis");
}

function analysisReportPath(project, bugId) {
  return path.join(analysisDir(project, bugId), "agent1_report.md");
}

async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

function parseCsvLine(line) {
  const fields = [];
  let current = "";
  let inQuotes = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && inQuotes && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      fields.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  fields.push(current);
  return fields.map((field) => field.trim());
}

function splitList(value) {
  return String(value ?? "")
    .split(";")
    .map((item) => item.trim())
    .filter(Boolean);
}

function testArtifactFromName(testName) {
  const [className, name] = String(testName).split("::");
  return {
    className: className ?? "",
    name: name ?? testName,
    assertion: "Provided by Defects4J tests.trigger metadata",
    output: "",
  };
}

function sourcePathForClass(className) {
  return `${String(className).replaceAll(".", "/")}.java`;
}

function inferBugType(project, modifiedClasses, triggeringTests) {
  const text = `${project} ${modifiedClasses.join(" ")} ${triggeringTests.join(" ")}`.toLowerCase();
  const tags = [];
  tags.push(modifiedClasses.length > 1 ? "multi-class" : "single-class");
  if (triggeringTests.length > 0) tags.push("test-driven");
  if (/math|solver|number|stat|fraction|complex|matrix/.test(text)) tags.push("algorithmic/numeric");
  if (/gson|jackson|generic|type|adapter|reflect/.test(text)) tags.push("type/generic resolution");
  if (/null|empty|bound|index|range|limit/.test(text)) tags.push("null/boundary condition");
  if (/config|locale|timezone|encoding|charset|path|file/.test(text)) tags.push("config/environment");
  if (/state|cache|mutat|series|dataset|collection/.test(text)) tags.push("state/side-effect");
  if (/api|parser|codec|format|serialize|deserialize/.test(text)) tags.push("API behavior");
  return tags.length ? tags.slice(0, 3) : ["unknown"];
}

async function queryBugRows(project) {
  const query = "bug.id,revision.id.buggy,revision.id.fixed,classes.modified,tests.trigger";
  const { stdout } = await runDefects4j(["query", "-p", project, "-q", query], { timeout: 120000 });
  return stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map(parseCsvLine)
    .map(([bugId, buggyVersion, fixedVersion, modifiedClasses, triggeringTests]) => ({
      bugId,
      buggyVersion,
      fixedVersion,
      modifiedClasses: splitList(modifiedClasses),
      triggeringTests: splitList(triggeringTests),
    }));
}

async function getBugMeta(project, bugId) {
  try {
    const rows = await queryBugRows(project);
    return rows.find((row) => row.bugId === bugId) ?? {
      bugId,
      buggyVersion: `${bugId}b`,
      fixedVersion: `${bugId}f`,
      modifiedClasses: [],
      triggeringTests: [],
    };
  } catch {
    return {
      bugId,
      buggyVersion: `${bugId}b`,
      fixedVersion: `${bugId}f`,
      modifiedClasses: [],
      triggeringTests: [],
    };
  }
}

async function getVerifiedOriginal(project, bugId) {
  const filePath = path.join(
    benchmarkRoot,
    "batches",
    DEFAULT_BATCH_ID,
    "originals",
    `${sanitizeProject(project)}-${sanitizeBugId(bugId)}`,
    "verified_original.json",
  );
  return readJsonIfExists(filePath);
}

async function captureFailingTestOutput(workspacePath, testId) {
  if (!workspacePath || !testId || !(await exists(workspacePath))) return "";
  try {
    const { stdout, stderr } = await runDefects4j(["test", "-t", testId], {
      cwd: workspacePath,
      timeout: 180000,
      allowedExitCodes: [0, 1],
    });
    return trimOutput(`${stdout}${stderr ? `\n${stderr}` : ""}`, 12000);
  } catch (error) {
    return error instanceof Error ? trimOutput(error.message, 12000) : "";
  }
}

async function enrichTaskWithObservedFailure(taskBundle) {
  const testId = taskBundle.agent_visible_task.failing_test_identifier;
  if (!testId || taskBundle.agent_visible_task.stack_trace) return taskBundle;
  if (taskBundle.task_type !== "original") return taskBundle;
  const workspacePath = checkoutPath(taskBundle.source.project, taskBundle.source.bug_id, "buggy");
  const stackTrace = await captureFailingTestOutput(workspacePath, testId);
  return {
    ...taskBundle,
    agent_visible_task: {
      ...taskBundle.agent_visible_task,
      stack_trace: stackTrace,
    },
  };
}

async function getAnalysis(project, bugId) {
  const reportPath = analysisReportPath(project, bugId);
  const reportExists = await exists(reportPath);
  return {
    exists: reportExists,
    path: reportExists ? path.relative(repoRoot, reportPath) : "",
    content: reportExists ? await fs.readFile(reportPath, "utf8") : "",
  };
}

async function getCheckoutStatus(project, bugId) {
  const buggyPath = checkoutPath(project, bugId, "buggy");
  const fixedPath = checkoutPath(project, bugId, "fixed");
  const buggy = await exists(buggyPath);
  const fixed = await exists(fixedPath);
  return {
    buggy,
    fixed,
    buggyPath: buggy ? path.relative(repoRoot, buggyPath) : "",
    fixedPath: fixed ? path.relative(repoRoot, fixedPath) : "",
  };
}

async function listVariantRuns(project, bugId) {
  const canonicalRecords = await discoverVariantRecords(variantsRoot);
  const canonicalRuns = [];
  for (const record of canonicalRecords) {
    if (record.project === project && record.bugId === String(bugId)) {
      canonicalRuns.push(
        canonicalRecordToRun(record, repoRoot, await exists(analysisReportPath(record.project, record.bugId))),
      );
    }
  }

  const slug = bugSlug(project, bugId);
  const slugRoot = path.join(variantsRoot, slug);
  if (!(await exists(slugRoot))) {
    return canonicalRuns.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }

  const levels = await fs.readdir(slugRoot, { withFileTypes: true });
  const runs = [...canonicalRuns];
  for (const levelEntry of levels) {
    if (!levelEntry.isDirectory() || !["L10", "L30"].includes(levelEntry.name)) continue;
    const levelRoot = path.join(slugRoot, levelEntry.name);
    const runEntries = await fs.readdir(levelRoot, { withFileTypes: true });
    for (const runEntry of runEntries) {
      if (!runEntry.isDirectory() || !/^run-\d{3}$/.test(runEntry.name)) continue;
      runs.push(await readVariantRun(project, bugId, levelEntry.name, runEntry.name));
    }
  }
  return runs.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

async function readJsonIfExists(filePath) {
  if (!(await exists(filePath))) return {};
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch {
    return {};
  }
}

async function readVariantRun(project, bugId, level, runName) {
  const slug = bugSlug(project, bugId);
  const runDir = path.join(variantsRoot, slug, level, runName);
  const metadata = await readJsonIfExists(path.join(runDir, "variant_run.json"));
  const analysis = await getAnalysis(project, bugId);
  const artifacts = [];
  for (const plan of artifactPlan) {
    for (const artifactName of plan.artifacts) {
      const artifactPath =
        artifactName === "agent1_report.md" && analysis.exists
          ? analysisReportPath(project, bugId)
          : path.join(runDir, artifactName);
      const ready = await exists(artifactPath);
      artifacts.push({
        name: artifactName,
        kind: artifactKinds[artifactName] ?? "report",
        status: ready ? "ready" : "queued",
        path: ready ? path.relative(repoRoot, artifactPath) : path.relative(repoRoot, artifactPath),
      });
    }
  }

  const workflow = artifactPlan.map((plan) => {
    const complete = plan.artifacts.every((artifactName) =>
      artifacts.some((artifact) => artifact.name === artifactName && artifact.status === "ready"),
    );
    return {
      id: plan.stepId,
      title: plan.title,
      status: complete ? "complete" : "pending",
      artifactNames: plan.artifacts,
    };
  });

  const validationComplete = workflow.at(-1)?.status === "complete";
  const status = validationComplete
    ? "validated"
    : workflow.some((step, index) => index >= 2 && step.status === "complete")
      ? "review"
      : workflow.some((step) => step.status === "complete")
        ? "running"
        : "queued";

  return {
    id: metadata.id ?? `${slug}-${level}-${runName}`,
    bugId: `${project}-${bugId}`,
    project,
    bugNumber: Number(bugId),
    variant_id: metadata.variant_id ?? `${slug}-${level}-${runName}`,
    level,
    dimension: metadata.dimension ?? "trigger-condition substitution",
    changedReasoningNode: metadata.changedReasoningNode ?? nodeForDimension[metadata.dimension] ?? "C: Input Constraint",
    status,
    outputPath: `${path.relative(repoRoot, runDir)}/`,
    candidateCount: metadata.candidateCount ?? 3,
    humanCheckpoint: metadata.humanCheckpoint ?? true,
    createdAt: metadata.createdAt ?? new Date(0).toISOString(),
    validation: validationComplete
      ? {
          baselinePass: "pass",
          variantFail: "fail",
          deterministicRuns: "pass",
        }
      : metadata.validation ?? {
          baselinePass: "pending",
          variantFail: "pending",
          deterministicRuns: "pending",
        },
    workflow,
    artifacts,
  };
}

async function statusForBug(project, bugId) {
  const checkout = await getCheckoutStatus(project, bugId);
  const analysis = await getAnalysis(project, bugId);
  const variantRuns = await listVariantRuns(project, bugId);
  if (variantRuns.length > 0) return "variant-created";
  if (analysis.exists) return "analyzed";
  if (checkout.buggy || checkout.fixed) return "checked-out";
  return "not-checked-out";
}

async function getBugDetail(project, bugId) {
  const meta = await getBugMeta(project, bugId);
  const checkout = await getCheckoutStatus(project, bugId);
  const analysis = await getAnalysis(project, bugId);
  const variants = await listVariantRuns(project, bugId);
  const bugType = inferBugType(project, meta.modifiedClasses, meta.triggeringTests);
  const modifiedClass = meta.modifiedClasses[0] ?? "";
  return {
    id: `${project}-${bugId}`,
    name: `${project}-${bugId}`,
    project,
    bugId: Number(bugId),
    bug_id: Number(bugId),
    baselineVersion: `fixed revision: ${meta.fixedVersion}`,
    buggyVersion: meta.buggyVersion,
    fixedVersion: meta.fixedVersion,
    status: await statusForBug(project, bugId),
    issue: `Defects4J ${project}-${bugId}`,
    modifiedClass,
    modifiedClasses: meta.modifiedClasses,
    buggyMethod: "Needs analysis",
    rootCause: analysis.exists ? "See agent1_report.md" : "Needs analysis",
    triggeringTests: meta.triggeringTests,
    relevantTests: [],
    sourceDirs: [],
    checkout,
    analysis,
    analysis_status: analysis.exists ? "analyzed" : "missing",
    bugType,
    reasoningType: analysis.exists ? bugType : ["needs analysis"],
    sourceFiles: [],
    tests: meta.triggeringTests.map(testArtifactFromName),
    diff: "",
    reasoningTree: [],
    variants,
  };
}

async function walkFiles(root, relativeDir = "", results = []) {
  const dir = path.join(root, relativeDir);
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (results.length >= 600) break;
    if ([".git", "target", "build", ".gradle", "node_modules"].includes(entry.name)) continue;
    const rel = path.join(relativeDir, entry.name);
    const abs = path.join(root, rel);
    if (entry.isDirectory()) {
      await walkFiles(root, rel, results);
    } else if (/\.(java|xml|properties|txt|md|csv|json|gradle|pom)$/.test(entry.name)) {
      const stat = await fs.stat(abs);
      if (stat.size <= 1024 * 1024) {
        results.push({
          path: rel.split(path.sep).join("/"),
          language: languageForFile(entry.name),
          size: stat.size,
        });
      }
    }
  }
  return results;
}

function languageForFile(fileName) {
  if (fileName.endsWith(".java")) return "java";
  if (fileName.endsWith(".xml") || fileName === "pom.xml") return "xml";
  if (fileName.endsWith(".json")) return "json";
  if (fileName.endsWith(".md")) return "markdown";
  if (fileName.endsWith(".csv")) return "csv";
  return "plaintext";
}

async function nextRunName(project, bugId, level) {
  const levelRoot = path.join(variantsRoot, bugSlug(project, bugId), level);
  await fs.mkdir(levelRoot, { recursive: true });
  for (let index = 1; index < 1000; index += 1) {
    const name = `run-${String(index).padStart(3, "0")}`;
    if (!(await exists(path.join(levelRoot, name)))) {
      return name;
    }
  }
  throw new ApiError(500, "No available run number below run-1000");
}

function placeholderArtifact(name, project, bugId, run) {
  const heading = name.replace(/\..*$/, "").replaceAll("_", " ");
  return `# ${heading}\n\nProject: ${project}\nBug: ${bugId}\nVariant: ${run.variant_id}\n\nPlaceholder artifact generated by the local D4J Variant Lab backend.\n`;
}

async function writeJson(filePath, data) {
  await fs.writeFile(filePath, `${JSON.stringify(data, null, 2)}\n`);
}

async function findCanonicalVariantRecordById(id, throwIfMissing = true) {
  let variantId;
  try {
    variantId = sanitizeVariantId(id);
  } catch (error) {
    if (!throwIfMissing) return null;
    throw new ApiError(400, error.message);
  }
  const records = await discoverVariantRecords(variantsRoot);
  const record = records.find((item) => item.variantId === variantId);
  if (!record && throwIfMissing) throw new ApiError(404, "Variant manifest not found");
  return record ?? null;
}

async function readVariantArtifact(record, artifactName, language) {
  const filePath = safeArtifactPath(record.dir, artifactName);
  if (!(await exists(filePath))) throw new ApiError(404, `${artifactName} not found`);
  return {
    variant_id: record.variantId,
    artifact: artifactName,
    language,
    path: path.relative(repoRoot, filePath),
    content: await fs.readFile(filePath, "utf8"),
  };
}

async function getActiveProjects() {
  const { stdout } = await runDefects4j(["pids"]);
  return stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map(sanitizeProject);
}

async function hasBugOne(project) {
  const { stdout } = await runDefects4j(["bids", "-p", project]);
  return stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .includes("1");
}

async function writeAttemptNote(project, bugId, variantId, status, reason) {
  const runDir = path.join(runsRoot, bugSlug(project, bugId));
  await fs.mkdir(runDir, { recursive: true });
  const payload = {
    project,
    bug_id: Number(bugId),
    variant_id: variantId,
    level: "L10",
    status,
    reason,
    updated_at: new Date().toISOString(),
  };
  await writeJson(path.join(runDir, "generation_status.json"), payload);
  await fs.writeFile(
    path.join(runDir, "generation_status.md"),
    `# ${project}-${bugId} L10 Generation Status

- Status: ${status}
- Variant ID: ${variantId}
- Reason: ${reason}

This record is an attempted benchmark-generation step, not an accepted semantic
variant. Accepted variants require the full validation gate.
`,
  );
}

async function markGeneratedAttempt(run, status, reason) {
  const record = await findCanonicalVariantRecordById(run.variant_id);
  const manifestPath = path.join(record.dir, "variant_manifest.json");
  const manifest = await readJsonIfExists(manifestPath);
  const updated = {
    ...manifest,
    status,
    reasoning: {
      ...(manifest.reasoning ?? {}),
      changed_node: status === "generation_failed" ? "no reviewed semantic candidate" : manifest.reasoning?.changed_node,
    },
    validation: { status: "not_run" },
    provenance: {
      ...(manifest.provenance ?? {}),
      failure_reason: reason,
    },
    updated_at: new Date().toISOString(),
  };
  await writeJson(manifestPath, updated);
  const tracePath = path.join(record.dir, "generation_trace.json");
  const trace = await readJsonIfExists(tracePath);
  await writeJson(tracePath, {
    ...(trace ?? {}),
    status,
    reason,
    updated_at: new Date().toISOString(),
  });
  await writeAttemptNote(record.project, record.bugId, record.variantId, status, reason);
  return await readVariantRecord(record.dir);
}

async function existingNonAcceptedRecord(project, bugId) {
  const records = await discoverVariantRecords(variantsRoot);
  return records.find(
    (record) =>
      record.project === project &&
      record.bugId === String(bugId) &&
      record.level === "L10" &&
      record.status !== "validated",
  );
}

async function attemptProjectL10(project, bugId, options = {}) {
  try {
    if (!(await hasBugOne(project))) {
      return { project, bug: Number(bugId), status: "skipped_no_bug_1", reason: "Project does not expose Bug 1" };
    }
    const beforeRecords = await discoverVariantRecords(variantsRoot);
    if (hasCanonicalValidatedBugVariant(beforeRecords, project, bugId, "L10")) {
      const validated = beforeRecords.find(
        (record) => record.project === project && record.bugId === String(bugId) && record.level === "L10" && record.status === "validated",
      );
      return {
        project,
        bug: Number(bugId),
        variant_id: validated?.variantId ?? "",
        status: "skipped_existing_validated",
        reason: "Validated canonical L10 variant already exists",
      };
    }

    const existingAttempt = await existingNonAcceptedRecord(project, bugId);
    if (existingAttempt && !options.forceNewAttempt) {
      return {
        project,
        bug: Number(bugId),
        variant_id: existingAttempt.variantId,
        status: existingAttempt.status,
        reason: "Existing non-validated attempt retained; use forceNewAttempt later to retry explicitly.",
      };
    }

    const reason =
      "Automated cross-project semantic variant synthesis is not implemented in this frontend/backend phase; refusing to fabricate an accepted benchmark artifact.";
    const run = await createIncompleteVariant({
      variantsRoot,
      repoRoot,
      project,
      bugId,
      level: "L10",
      dimension: "trigger-condition substitution",
      candidateCount: 3,
      humanCheckpoint: true,
    });
    const record = await markGeneratedAttempt(run, "generation_failed", reason);
    return {
      project,
      bug: Number(bugId),
      variant_id: record.variantId,
      status: "generation_failed",
      reason,
    };
  } catch (error) {
    const reason = error instanceof Error ? error.message : "Unknown generation attempt failure";
    return { project, bug: Number(bugId), status: "environment_blocked", reason };
  }
}

async function getAgentProfileOrThrow(agentId) {
  let safeId;
  try {
    safeId = sanitizeBenchmarkId(agentId, "agent id");
  } catch (error) {
    throw new ApiError(400, error.message);
  }
  const adapterStatus = await miniSweAgentAdapter.inspectAvailability(process.env);
  const agents = (await listAgentProfiles(benchmarkRoot, process.env)).map((profile) =>
    withAgentRuntimeStatus(profile, { env: process.env, adapter: adapterStatus }),
  );
  const agent = agents.find((profile) => profile.agent_id === safeId);
  if (!agent) throw new ApiError(404, "Agent profile not found");
  return agent;
}

function benchmarkDebugOverride(body) {
  return (
    body?.debug_allow_unreproduced_variant === true ||
    body?.allow_unreproduced_variant === true ||
    body?.debug?.allow_unreproduced_variant === true
  );
}

function compactTimestamp(date = new Date()) {
  return date.toISOString().replace(/[-:.]/g, "").replace("T", "T").replace("Z", "Z");
}

function assertVariantCanEnterBenchmark(record, body) {
  const eligibility = variantBenchmarkEligibility(record, {
    debug_allow_unreproduced_variant: benchmarkDebugOverride(body),
  });
  if (!eligibility.ok) {
    throw new ApiError(409, `Variant is not benchmark-eligible: ${eligibility.reasons.join("; ")}`);
  }
  return eligibility;
}

async function buildBenchmarkTaskFromRequest(body) {
  const taskType = String(body?.task_type ?? body?.taskType ?? "original");
  if (taskType === "original") {
    const project = sanitizeProject(body?.original?.project ?? body?.project);
    const bugId = sanitizeBugId(body?.original?.bug_id ?? body?.original?.bugId ?? body?.bug_id ?? body?.bugId);
    const meta = await getBugMeta(project, bugId);
    const verified = await getVerifiedOriginal(project, bugId);
    const verifiedMeta = verified
      ? {
          ...meta,
          triggeringTests: verified.triggering_tests ?? meta.triggeringTests,
          modifiedClasses: verified.modified_production_classes ?? meta.modifiedClasses,
          goldMethods: verified.gold_methods ?? [],
        }
      : meta;
    return enrichTaskWithObservedFailure(buildOriginalAgentTask({ project, bugId, meta: verifiedMeta, checkoutRoot }));
  }
  if (taskType === "variant") {
    const variantId = body?.variant_id ?? body?.variantId ?? body?.variant?.variant_id;
    const record = await findCanonicalVariantRecordById(variantId);
    assertVariantCanEnterBenchmark(record, body);
    return enrichTaskWithObservedFailure(buildVariantAgentTask({ record, checkoutRoot }));
  }
  throw new ApiError(400, "Invalid benchmark task_type");
}

async function createBenchmarkRunsForRequest(body) {
  const agent = await getAgentProfileOrThrow(body?.agent_id ?? body?.agentId);
  const taskBundle = await buildBenchmarkTaskFromRequest(body);
  const repeatCount = Math.max(1, Math.min(20, Number(body?.repeats ?? 1)));
  const budget = normalizeBudget(body?.budget ?? agent.defaults);
  const runs = [];
  for (let repeatIndex = 1; repeatIndex <= repeatCount; repeatIndex += 1) {
    runs.push(
      await createBenchmarkRun({
        benchmarkRoot,
        repoRoot,
        agent,
        taskBundle,
        budget,
        repeat_index: repeatIndex,
        adapter: miniSweAgentAdapter,
      }),
    );
  }
  return runs;
}

async function createBenchmarkPairRunsForRequest(body) {
  const agent = await getAgentProfileOrThrow(body?.agent_id ?? body?.agentId);
  const project = sanitizeProject(body?.original?.project);
  const bugId = sanitizeBugId(body?.original?.bug_id ?? body?.original?.bugId);
  const variantRecord = await findCanonicalVariantRecordById(body?.variant_id ?? body?.variantId);
  if (variantRecord.project !== project || variantRecord.bugId !== bugId) {
    throw new ApiError(400, "Variant does not match the selected original source bug");
  }
  assertVariantCanEnterBenchmark(variantRecord, body);
  const meta = await getBugMeta(project, bugId);
  const budget = normalizeBudget(body?.budget ?? agent.defaults);
  const originalTask = await enrichTaskWithObservedFailure(buildOriginalAgentTask({ project, bugId, meta, checkoutRoot }));
  const variantTask = await enrichTaskWithObservedFailure(buildVariantAgentTask({ record: variantRecord, checkoutRoot }));
  return [
    await createBenchmarkRun({ benchmarkRoot, repoRoot, agent, taskBundle: originalTask, budget, repeat_index: 1, adapter: miniSweAgentAdapter }),
    await createBenchmarkRun({ benchmarkRoot, repoRoot, agent, taskBundle: variantTask, budget, repeat_index: 1, adapter: miniSweAgentAdapter }),
  ];
}

function benchmarkMetricsForBatch(run) {
  const metrics = run.manifest.metrics ?? {};
  return {
    gold_rank: run.manifest.status === "completed" ? run.evaluation.gold_rank : null,
    hit_at_1: run.manifest.status === "completed" ? run.evaluation.gold_rank === 1 : null,
    hit_at_5: run.manifest.status === "completed" ? run.evaluation.hit_at_5 : null,
    hit_at_10: run.manifest.status === "completed" ? run.evaluation.hit_at_10 : null,
    mrr: run.manifest.status === "completed" && Number.isInteger(run.evaluation.gold_rank) ? 1 / run.evaluation.gold_rank : null,
    tool_calls: metrics.tool_call_count ?? null,
    searches: metrics.search_count ?? null,
    unique_files_read: metrics.unique_files_read ?? null,
    production_files_read: metrics.production_files_read ?? null,
    test_files_read: metrics.test_files_read ?? null,
    test_runs: metrics.test_run_count ?? null,
    duration_ms: parseBenchmarkDurationMs(run.commands),
    gold_file_read: metrics.gold_file_read ?? null,
    first_gold_file_read_position: metrics.first_gold_file_read_position ?? null,
  };
}

function containsLiteral(haystack, needle) {
  return Boolean(needle) && String(haystack ?? "").toLowerCase().includes(String(needle).toLowerCase());
}

function shortcutAuditForRun(run) {
  const task = run.task ?? {};
  const testSource = String(task.failing_test_source ?? "");
  const stackTrace = String(task.stack_trace ?? "");
  const testName = String(task.failing_test_identifier ?? "").split("::").at(-1) ?? "";
  const searches = (run.trajectory ?? []).filter((event) => event.type === "search");
  const goldMethods = run.evaluation?.gold_methods ?? [];
  const methodNames = goldMethods.map((gold) => gold.method);
  const classNames = goldMethods.flatMap((gold) => [gold.class, gold.class.split(".").at(-1)]).filter(Boolean);
  const goldFiles = goldMethods.map((gold) => gold.file).filter(Boolean);
  const firstMethodEvent = (run.trajectory ?? []).find((event) =>
    methodNames.some((method) => containsLiteral(event.target, method)),
  );
  return {
    schema_version: "d4j-shortcut-audit/v1",
    task_id: run.manifest.task_id,
    run_id: run.id,
    evidence_scope: "literal task-input and observable tool-trajectory matching only",
    gold_method_in_test_source: methodNames.some((method) => containsLiteral(testSource, method)),
    gold_class_in_test_source: classNames.some((className) => containsLiteral(testSource, className)),
    gold_method_in_test_name: methodNames.some((method) => containsLiteral(testName, method)),
    gold_class_in_stack_trace: classNames.some((className) => containsLiteral(stackTrace, className)),
    gold_method_in_stack_trace: methodNames.some((method) => containsLiteral(stackTrace, method) || (method === goldMethods[0]?.class?.split(".").at(-1) && containsLiteral(stackTrace, "<init>"))),
    failure_message_names_gold_method: methodNames.some((method) => containsLiteral(stackTrace.split("\n").slice(0, 8).join("\n"), method)),
    trigger_directly_calls_gold_method: methodNames.some((method) => new RegExp(`\\b${method.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&")}\\s*\\(`).test(testSource)),
    gold_file_obvious_from_stack_trace: goldFiles.some((file) => containsLiteral(stackTrace, path.basename(file))),
    searched_exact_test_name: searches.some((event) => containsLiteral(event.target, testName)),
    searched_exact_exception_message: searches.some((event) => stackTrace.split("\n").some((line) => line.length > 20 && containsLiteral(event.target, line.trim()))),
    searched_gold_method_name: searches.some((event) => methodNames.some((method) => containsLiteral(event.target, method))),
    first_gold_file_open_position: run.manifest.metrics?.first_gold_file_read_position ?? null,
    first_gold_method_identified_position: firstMethodEvent?.sequence ?? null,
    audited_at: new Date().toISOString(),
  };
}

let batchEventWrite = Promise.resolve();

function safeBatchLogText(value) {
  return String(value ?? "")
    .replace(/sk-proj-[A-Za-z0-9_-]+/g, "[redacted]")
    .replace(/[\r\n]+/g, " ")
    .trim();
}

function emitBatchEvent(batchId, { event, project = null, level = null, stage, status, reason = null, artifactPath = null }) {
  const timestamp = new Date().toISOString();
  const task = project ? `${project}-1${level && level !== "Original" ? ` ${level}` : " Original"}` : batchId;
  const current = `${task} ${stage}`;
  const record = {
    timestamp,
    event,
    project,
    bug: project ? 1 : null,
    level,
    stage,
    status,
    reason: reason ? safeBatchLogText(reason) : null,
    artifact_path: artifactPath,
  };
  multiFamilyBatchJob = { ...multiFamilyBatchJob, batch_id: batchId, current, updated_at: timestamp };
  const suffix = [record.reason, record.artifact_path].filter(Boolean).join(" | ");
  console.log(`[batch:${batchId}] ${timestamp} [${event}] ${task} ${stage} — ${status}${suffix ? ` — ${suffix}` : ""}`);
  const eventPath = path.join(benchmarkRoot, "batches", batchId, "batch_events.jsonl");
  batchEventWrite = batchEventWrite
    .then(async () => {
      await fs.mkdir(path.dirname(eventPath), { recursive: true });
      await fs.appendFile(eventPath, `${JSON.stringify(record)}\n`, { mode: 0o600 });
    })
    .catch((error) => console.error(`[batch:${batchId}] could not persist event: ${safeBatchLogText(error.message)}`));
}

function batchHeartbeat(batchId, current, context = {}) {
  emitBatchEvent(batchId, {
    event: "HEARTBEAT",
    project: context.project ?? null,
    level: context.level ?? null,
    stage: context.stage ?? current,
    status: "running",
    reason: context.reason ?? current,
    artifactPath: context.artifactPath ?? null,
  });
}

function startBatchHeartbeat(batchId, context) {
  const timer = setInterval(() => batchHeartbeat(batchId, `${context.stage} still running`, context), 45000);
  timer.unref();
  return () => clearInterval(timer);
}

async function checkpointBenchmarkRun(batchId, entry, run) {
  const shortcutAudit = shortcutAuditForRun(run);
  await fs.writeFile(path.join(run.run_dir, "shortcut_audit.json"), `${JSON.stringify(shortcutAudit, null, 2)}\n`, { mode: 0o600 });
  await checkpointBatchEntry(benchmarkRoot, batchId, entry.key, {
    current_stage: "benchmark_complete",
    resume_from: null,
    benchmark_status: run.manifest.status,
    benchmark_run_id: run.id,
    metrics: benchmarkMetricsForBatch(run),
    ranking: run.manifest.status === "completed" ? run.ranking?.structured_submission?.predictions ?? [] : [],
    shortcut_audit: shortcutAudit,
    reasoning_workflow_path: `${run.artifact_path}reasoning_workflow.json`,
    artifact_paths: [run.artifact_path],
    failure_reason: run.manifest.status === "completed" ? entry.failure_reason ?? null : run.manifest.status_reason,
  });
}

async function runBatchBenchmark(batchId, entry) {
  if (entry.benchmark_status && entry.benchmark_status !== "not_run" && entry.benchmark_status !== "running") {
    emitBatchEvent(batchId, {
      event: "SKIPPED",
      project: entry.project,
      level: entry.level,
      stage: "localization",
      status: entry.benchmark_status,
      reason: "Existing terminal localization result preserved.",
      artifactPath: entry.artifact_paths?.at(-1) ?? null,
    });
    return;
  }
  await checkpointBatchEntry(benchmarkRoot, batchId, entry.key, {
    current_stage: "benchmark",
    resume_from: "benchmark",
    benchmark_status: "running",
  });
  emitBatchEvent(batchId, {
    event: "START",
    project: entry.project,
    level: entry.level,
    stage: "localization",
    status: "running",
  });
  const stopHeartbeat = startBatchHeartbeat(batchId, { project: entry.project, level: entry.level, stage: "localization" });
  try {
    const request = {
      agent_id: "mini-swe-gpt56",
      task_type: entry.task_kind === "original" ? "original" : "variant",
      original: entry.task_kind === "original" ? { project: entry.project, bug_id: entry.bug } : undefined,
      variant_id: entry.task_kind === "private_variant" ? entry.variant_id : undefined,
      budget: { max_tool_calls: 50, max_test_runs: 5, timeout_seconds: 300 },
      repeats: 1,
    };
    const runs = await createBenchmarkRunsForRequest(request);
    await checkpointBenchmarkRun(batchId, entry, runs[0]);
    emitBatchEvent(batchId, {
      event: runs[0].manifest.status === "completed" ? "DONE" : "FAILED",
      project: entry.project,
      level: entry.level,
      stage: "localization",
      status: runs[0].manifest.status,
      reason: runs[0].manifest.status_reason,
      artifactPath: runs[0].artifact_path,
    });
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    await checkpointBatchEntry(benchmarkRoot, batchId, entry.key, {
      current_stage: "benchmark_complete",
      resume_from: null,
      benchmark_status: "failed",
      failure_reason: reason,
    });
    emitBatchEvent(batchId, {
      event: "FAILED",
      project: entry.project,
      level: entry.level,
      stage: "localization",
      status: "failed",
      reason,
    });
  } finally {
    stopHeartbeat();
  }
  await writeBatchOutputs(benchmarkRoot, batchId);
  emitBatchEvent(batchId, {
    event: "CHECKPOINT",
    project: entry.project,
    level: entry.level,
    stage: "localization",
    status: "persisted",
  });
}

async function runMultiFamilyBatch(batchId = DEFAULT_BATCH_ID) {
  await ensureBatch(benchmarkRoot, batchId);
  let { manifest: initialManifest } = await readBatch(benchmarkRoot, batchId);
  const projectOrder = initialManifest.project_order ?? [];
  const levelOrder = initialManifest.level_order ?? [];
  for (const project of projectOrder) {
    let { manifest } = await readBatch(benchmarkRoot, batchId);
    const original = manifest.originals.find((entry) => entry.project === project);
    if (!original || original.status !== "verified") {
      for (const level of levelOrder) {
        const entry = manifest.variants.find((item) => item.project === project && item.level === level);
        if (entry?.status === "pending") {
          await checkpointBatchEntry(benchmarkRoot, batchId, entry.key, {
            status: "environment_blocked",
            current_stage: "complete",
            resume_from: null,
            generation_status: "environment_blocked",
            failure_reason: "Original bug verification did not complete.",
          });
          emitBatchEvent(batchId, {
            event: "SKIPPED",
            project,
            level,
            stage: "generation",
            status: "environment_blocked",
            reason: "Original bug verification did not complete.",
          });
        }
      }
      continue;
    }

    for (const level of levelOrder) {
      ({ manifest } = await readBatch(benchmarkRoot, batchId));
      const entry = manifest.variants.find((item) => item.project === project && item.level === level);
      if (!entry || entry.status !== "pending" && entry.status !== "running") {
        if (entry) {
          emitBatchEvent(batchId, {
            event: "SKIPPED",
            project,
            level,
            stage: "generation",
            status: entry.status,
            reason: "Existing terminal generation result preserved.",
            artifactPath: entry.artifact_paths?.[0] ?? null,
          });
        }
        continue;
      }
      const prerequisiteLevel = { L50: "L30", L70: "L50", L90: "L70" }[level];
      if (prerequisiteLevel) {
        const prerequisite = manifest.variants.find((item) => item.project === project && item.level === prerequisiteLevel);
        if (prerequisite?.status !== "validated") {
          await checkpointBatchEntry(benchmarkRoot, batchId, entry.key, {
            status: "not_attempted_due_to_dependency",
            generation_status: "not_attempted_due_to_dependency",
            current_stage: "complete",
            resume_from: null,
            reasoning_level_status: "depth_unachievable",
            failure_reason: `${level} was not forced because the required ${prerequisiteLevel} prerequisite was not accepted.`,
          });
          emitBatchEvent(batchId, {
            event: "SKIPPED",
            project,
            level,
            stage: "generation",
            status: "not_attempted_due_to_dependency",
            reason: `${prerequisiteLevel} prerequisite was not accepted.`,
          });
          await writeBatchOutputs(benchmarkRoot, batchId);
          continue;
        }
      }

      await checkpointBatchEntry(benchmarkRoot, batchId, entry.key, {
        status: "running",
        generation_status: "running",
        current_stage: "candidate_generation",
        resume_from: "candidate_generation",
        failure_reason: null,
      });
      emitBatchEvent(batchId, { event: "START", project, level, stage: "generation", status: "running" });
      const stopHeartbeat = startBatchHeartbeat(batchId, { project, level, stage: "generation" });
      let validationStarted = false;
      try {
        const result = await constructVariantAttempt({
          repoRoot,
          checkoutRoot,
          variantsRoot,
          batchDir: path.join(benchmarkRoot, "batches", batchId),
          project,
          level,
          env: process.env,
          heartbeat: (message) => {
            if (!validationStarted && message.includes("fresh baseline checkout")) {
              validationStarted = true;
              emitBatchEvent(batchId, { event: "DONE", project, level, stage: "generation", status: "candidate_selected" });
              emitBatchEvent(batchId, { event: "START", project, level, stage: "validation", status: "running" });
            }
            batchHeartbeat(batchId, message, { project, level, stage: validationStarted ? "validation" : "generation", reason: message });
          },
        });
        const patch = {
          status: result.status,
          generation_status: result.status,
          validation_status: result.status === "validated" ? "validated" : result.status === "validation_failed" ? "failed" : "not_run",
          reproducibility_status: result.status === "validated" ? "passed" : null,
          consistency: result.status === "validated" ? true : null,
          benchmark_eligible: result.status === "validated",
          current_stage: result.status === "validated" ? "benchmark" : "complete",
          resume_from: result.status === "validated" ? "benchmark" : null,
          variant_id: result.variantId ?? null,
          artifact_paths: [result.canonicalDir ?? result.attemptDir].filter(Boolean).map((item) => `${path.relative(repoRoot, item)}/`),
          failure_reason: result.status === "validated" ? null : result.reason,
        };
        if (result.metadata) {
          Object.assign(patch, {
            reasoning_level: level,
            semantic_inference_steps: result.metadata.semantic_inference_steps,
            shortest_reasoning_path: result.metadata.shortest_reasoning_path,
            shortcut_risks: result.metadata.shortcut_risks ?? [],
            reasoning_level_status: "validated",
            root_cause: result.metadata.semantic_root_cause,
            gold_method: result.gold,
          });
        }
        await checkpointBatchEntry(benchmarkRoot, batchId, entry.key, patch);
        emitBatchEvent(batchId, {
          event: result.status === "validated" ? "DONE" : result.status === "depth_unachievable" ? "SKIPPED" : "FAILED",
          project,
          level,
          stage: validationStarted ? "validation" : "generation",
          status: result.status,
          reason: result.status === "validated" ? "Canonical reproducibility gate passed." : result.reason,
          artifactPath: patch.artifact_paths[0] ?? null,
        });
      } catch (error) {
        const reason = error instanceof Error ? error.message : String(error);
        await checkpointBatchEntry(benchmarkRoot, batchId, entry.key, {
          status: "generation_failed",
          generation_status: "generation_failed",
          current_stage: "complete",
          resume_from: null,
          failure_reason: reason,
        });
        emitBatchEvent(batchId, { event: "FAILED", project, level, stage: validationStarted ? "validation" : "generation", status: "generation_failed", reason });
      } finally {
        stopHeartbeat();
      }
      await writeBatchOutputs(benchmarkRoot, batchId);
      emitBatchEvent(batchId, { event: "CHECKPOINT", project, level, stage: "construction", status: "persisted" });
    }

    ({ manifest } = await readBatch(benchmarkRoot, batchId));
    const refreshedOriginal = manifest.originals.find((entry) => entry.project === project);
    await runBatchBenchmark(batchId, refreshedOriginal);
    ({ manifest } = await readBatch(benchmarkRoot, batchId));
    for (const level of levelOrder) {
      const variant = manifest.variants.find((entry) => entry.project === project && entry.level === level);
      if (variant?.status === "validated") await runBatchBenchmark(batchId, variant);
    }
  }
  await writeBatchOutputs(benchmarkRoot, batchId);
  await batchEventWrite;
  emitBatchEvent(batchId, { event: "DONE", stage: "batch", status: "completed" });
  await batchEventWrite;
}

async function getBenchmarkRunOrThrow(value) {
  let runId;
  try {
    runId = sanitizeBenchmarkId(value, "run id");
  } catch (error) {
    throw new ApiError(400, error.message);
  }
  const record = await findBenchmarkRunById(benchmarkRoot, repoRoot, runId, false);
  if (!record) throw new ApiError(404, "Benchmark run not found");
  return record;
}

app.get("/api/env", async (_, res, next) => {
  try {
    res.json(await getEnvStatus());
  } catch (error) {
    next(error);
  }
});

app.get("/api/projects", async (_, res, next) => {
  try {
    const { stdout } = await runDefects4j(["pids"]);
    res.json(stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean));
  } catch (error) {
    next(error);
  }
});

app.get("/api/projects/:project/bugs", async (req, res, next) => {
  try {
    const project = sanitizeProject(req.params.project);
    const { stdout } = await runDefects4j(["bids", "-p", project]);
    res.json(stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean).map(Number));
  } catch (error) {
    next(error);
  }
});

app.get("/api/agents", async (_, res, next) => {
  try {
    const adapterStatus = await miniSweAgentAdapter.inspectAvailability(process.env);
    const agents = (await listAgentProfiles(benchmarkRoot, process.env)).map((profile) =>
      withAgentRuntimeStatus(profile, { env: process.env, adapter: adapterStatus }),
    );
    res.json({
      protocol: benchmarkProtocol,
      agents,
      adapters: {
        mini_swe_agent: adapterStatus,
      },
    });
  } catch (error) {
    next(error);
  }
});

app.post("/api/agents/mini-swe-agent/smoke-test", async (req, res, next) => {
  try {
    const agent = await getAgentProfileOrThrow(req.body?.agent_id ?? req.body?.agentId ?? "mini-swe-agent-openai-gpt-5-6");
    const timeoutSeconds = normalizeBudget({
      ...agent.defaults,
      timeout_seconds: req.body?.timeout_seconds ?? req.body?.timeoutSeconds ?? agent.defaults?.timeout_seconds,
    }).timeout_seconds;
    const runId = `smoke-${compactTimestamp()}`;
    const runDir = path.join(benchmarkRoot, "_smoke", "mini-swe-agent", runId);
    const result = await miniSweAgentAdapter.smokeTest({
      runDir,
      agent,
      executionTimeoutSeconds: timeoutSeconds,
    });
    res.json({
      ...result,
      run_id: runId,
      artifact_path: `${path.relative(repoRoot, runDir)}/`,
    });
  } catch (error) {
    next(error);
  }
});

app.post("/api/agents", async (req, res, next) => {
  try {
    if (!assertNoCredentialFields(req.body ?? {})) {
      throw new ApiError(400, "Do not submit API keys, tokens, or secrets through the frontend");
    }
    const profile = await saveAgentProfile(benchmarkRoot, req.body ?? {}, process.env);
    res.json(profile);
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-runs", async (_, res, next) => {
  try {
    const records = await discoverBenchmarkRunRecords(benchmarkRoot, repoRoot);
    res.json({
      protocol: benchmarkProtocol,
      summary: summarizeBenchmarkRuns(records),
      groups: groupBenchmarkRuns(records),
      runs: records.map(recordToRunSummary),
    });
  } catch (error) {
    next(error);
  }
});

app.post("/api/benchmark-runs", async (req, res, next) => {
  try {
    const details = await createBenchmarkRunsForRequest(req.body ?? {});
    res.json({ runs: details.map(recordToRunSummary), details });
  } catch (error) {
    next(error);
  }
});

app.post("/api/benchmark-runs/pair", async (req, res, next) => {
  try {
    const details = await createBenchmarkPairRunsForRequest(req.body ?? {});
    res.json({
      pair_id: details.map((detail) => detail.id).join("__PAIR__"),
      runs: details.map(recordToRunSummary),
      details,
    });
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-runs/:runId", async (req, res, next) => {
  try {
    let runId;
    try {
      runId = sanitizeBenchmarkId(req.params.runId, "run id");
    } catch (error) {
      throw new ApiError(400, error.message);
    }
    const record = await findBenchmarkRunById(benchmarkRoot, repoRoot, runId, false);
    if (!record) throw new ApiError(404, "Benchmark run not found");
    const analysis = await buildAccuracyAnalysis({ benchmarkRoot, repoRoot });
    const canonical = analysis.run_level_results.find((item) => item.run_id === record.id);
    res.json({
      ...record,
      shortcut_audit: canonical?.shortcut_audit ?? record.shortcut_audit ?? null,
    });
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-runs/:runId/ranking", async (req, res, next) => {
  try {
    const record = await getBenchmarkRunOrThrow(req.params.runId);
    res.json(await readBenchmarkArtifact(record, "ranking.json"));
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-runs/:runId/trajectory", async (req, res, next) => {
  try {
    const record = await getBenchmarkRunOrThrow(req.params.runId);
    res.json({ run_id: record.id, trajectory: record.trajectory });
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-runs/:runId/reasoning-workflow", async (req, res, next) => {
  try {
    const record = await getBenchmarkRunOrThrow(req.params.runId);
    res.json(record.reasoning_workflow);
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-batches/:batchId", async (req, res, next) => {
  try {
    const batchId = req.params.batchId || DEFAULT_BATCH_ID;
    await ensureBatch(benchmarkRoot, batchId);
    const output = await writeBatchOutputs(benchmarkRoot, batchId);
    const eventText = await fs.readFile(path.join(output.dir, "batch_events.jsonl"), "utf8").catch(() => "");
    const events = eventText
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-200)
      .map((line) => JSON.parse(line));
    res.json({
      manifest: output.manifest,
      variant_matrix: output.matrix,
      benchmark_results: output.benchmarkRows,
      original_vs_variant: output.comparison,
      depth_summary: output.depth,
      acc1_matrix: output.acc1,
      workflow_summary: output.workflow,
      file_overlap_matrices: output.fileOverlapMatrices,
      events,
      job: multiFamilyBatchJob.batch_id === batchId ? multiFamilyBatchJob : null,
      artifact_path: `${path.relative(repoRoot, output.dir)}/`,
    });
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark/accuracy", async (req, res, next) => {
  try {
    const metric = String(req.query.metric ?? "at1");
    if (!accuracyMetricNames.has(metric)) throw new ApiError(400, "Unsupported accuracy metric");
    const { analysis, outputDir } = await writeAccuracyAnalysis({ benchmarkRoot, repoRoot });
    res.json({
      ...selectAccuracyMetric(analysis, metric),
      artifact_path: `${path.relative(repoRoot, outputDir)}/`,
    });
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark/accuracy/:family/:depth", async (req, res, next) => {
  try {
    const metric = String(req.query.metric ?? "at1");
    if (!accuracyMetricNames.has(metric)) throw new ApiError(400, "Unsupported accuracy metric");
    const family = sanitizeBenchmarkId(req.params.family, "family");
    const depth = sanitizeBenchmarkId(req.params.depth, "depth").toUpperCase();
    const { analysis } = await writeAccuracyAnalysis({ benchmarkRoot, repoRoot });
    const selected = selectAccuracyMetric(analysis, metric);
    const row = selected.matrix.rows.find((item) => item.family.toLowerCase() === family.toLowerCase());
    const cell = row?.cells?.[depth];
    if (!cell) throw new ApiError(404, "Accuracy cell not found");
    res.json({
      metric,
      family: row.family,
      depth,
      value: cell.selected.value,
      numerator: cell.selected.numerator ?? null,
      denominator: cell.selected.denominator,
      availability: cell.availability,
      exclusion_reasons: cell.exclusion_reasons,
      cell,
    });
  } catch (error) {
    next(error);
  }
});

app.post("/api/benchmark-batches/:batchId/resume", async (req, res, next) => {
  try {
    const batchId = sanitizeBenchmarkId(req.params.batchId || DEFAULT_BATCH_ID, "batch id");
    if (multiFamilyBatchJob.running) {
      throw new ApiError(409, `Batch ${multiFamilyBatchJob.batch_id} is already running`);
    }
    const startedAt = new Date().toISOString();
    multiFamilyBatchJob = {
      running: true,
      batch_id: batchId,
      current: "starting",
      started_at: startedAt,
      updated_at: startedAt,
      error: null,
    };
    runMultiFamilyBatch(batchId)
      .catch((error) => {
        multiFamilyBatchJob = {
          ...multiFamilyBatchJob,
          error: error instanceof Error ? error.message : String(error),
        };
      })
      .finally(() => {
        multiFamilyBatchJob = {
          ...multiFamilyBatchJob,
          running: false,
          current: "idle",
          updated_at: new Date().toISOString(),
        };
      });
    res.status(202).json({ batch_id: batchId, status: "running", started_at: startedAt });
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-runs/:runId/files", async (req, res, next) => {
  try {
    const record = await getBenchmarkRunOrThrow(req.params.runId);
    res.json({ run_id: record.id, files: record.files });
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-runs/:runId/commands", async (req, res, next) => {
  try {
    const record = await getBenchmarkRunOrThrow(req.params.runId);
    res.json({ run_id: record.id, content: await readBenchmarkArtifact(record, "commands.log") });
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-runs/:runId/tests", async (req, res, next) => {
  try {
    const record = await getBenchmarkRunOrThrow(req.params.runId);
    res.json({ run_id: record.id, test_runs: record.test_runs });
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-comparisons/pair", async (req, res, next) => {
  try {
    const records = await discoverBenchmarkRunRecords(benchmarkRoot, repoRoot);
    let first = null;
    let second = null;
    if (req.query.originalRunId && req.query.variantRunId) {
      first = await getBenchmarkRunOrThrow(req.query.originalRunId);
      second = await getBenchmarkRunOrThrow(req.query.variantRunId);
    } else if (req.query.runId) {
      first = await getBenchmarkRunOrThrow(req.query.runId);
      second = matchingPairForRun(first, records);
    }
    if (!first || !second) {
      res.json({ mode: "original_vs_variant", rows: [], file_overlap: null, message: "No matching pair found." });
      return;
    }
    const original = first.manifest.task_type === "original" ? first : second;
    const variant = first.manifest.task_type === "variant" ? first : second;
    res.json(compareOriginalVariantRuns(original, variant));
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-comparisons/agents", async (req, res, next) => {
  try {
    const records = await discoverBenchmarkRunRecords(benchmarkRoot, repoRoot);
    let taskId = req.query.taskId ? sanitizeBenchmarkId(req.query.taskId, "task id") : "";
    if (!taskId && req.query.runId) {
      const record = await getBenchmarkRunOrThrow(req.query.runId);
      taskId = record.manifest.task_id;
    }
    const matching = taskId ? records.filter((record) => record.manifest.task_id === taskId) : [];
    res.json(compareAgentRuns(matching));
  } catch (error) {
    next(error);
  }
});

app.get("/api/benchmark-calibrations/chart-1-depth-ladder", async (_, res, next) => {
  try {
    const [records, variantRecords] = await Promise.all([
      discoverBenchmarkRunRecords(benchmarkRoot, repoRoot),
      discoverVariantRecords(variantsRoot),
    ]);
    res.json(buildChartDepthLadder(records, variantRecords));
  } catch (error) {
    next(error);
  }
});

app.get("/api/bugs", async (_, res, next) => {
  try {
    const { stdout } = await runDefects4j(["pids"]);
    const projects = stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    const summaries = [];
    for (const rawProject of projects) {
      const project = sanitizeProject(rawProject);
      const bids = await runDefects4j(["bids", "-p", project]);
      for (const id of bids.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)) {
        const bugId = sanitizeBugId(id);
        summaries.push({
          id: `${project}-${bugId}`,
          name: `${project}-${bugId}`,
          project,
          bugId: Number(bugId),
          baselineVersion: `${bugId}f`,
          status: await statusForBug(project, bugId),
          issue: `Defects4J ${project}-${bugId}`,
        });
      }
    }
    res.json(summaries);
  } catch (error) {
    next(error);
  }
});

app.get("/api/bugs/:project/:bugId", async (req, res, next) => {
  try {
    const project = sanitizeProject(req.params.project);
    const bugId = sanitizeBugId(req.params.bugId);
    res.json(await getBugDetail(project, bugId));
  } catch (error) {
    next(error);
  }
});

app.post("/api/bugs/:project/:bugId/checkout", async (req, res, next) => {
  try {
    const project = sanitizeProject(req.params.project);
    const bugId = sanitizeBugId(req.params.bugId);
    const version = sanitizeVersion(req.body?.version ?? "f");
    const force = Boolean(req.body?.force);
    const target = checkoutPath(project, bugId, version);
    const targetExists = await exists(target);
    if (targetExists) {
      res.json({
        project,
        bugId: Number(bugId),
        version,
        checkoutPath: path.relative(repoRoot, target),
        fileTreeRoot: path.relative(repoRoot, target),
        status: force ? "exists-not-overwritten" : "exists",
      });
      return;
    }

    await fs.mkdir(path.dirname(target), { recursive: true });
    await runDefects4j(["checkout", "-p", project, "-v", `${bugId}${version === "buggy" ? "b" : "f"}`, "-w", target], {
      timeout: 300000,
    });
    res.json({
      project,
      bugId: Number(bugId),
      version,
      checkoutPath: path.relative(repoRoot, target),
      fileTreeRoot: path.relative(repoRoot, target),
      status: "checked-out",
    });
  } catch (error) {
    next(error);
  }
});

app.get("/api/bugs/:project/:bugId/files", async (req, res, next) => {
  try {
    const project = sanitizeProject(req.params.project);
    const bugId = sanitizeBugId(req.params.bugId);
    const version = sanitizeVersion(req.query.version ?? "fixed");
    const root = checkoutPath(project, bugId, version);
    if (!(await exists(root))) {
      res.json({ checkedOut: false, checkoutPath: path.relative(repoRoot, root), files: [] });
      return;
    }
    res.json({
      checkedOut: true,
      checkoutPath: path.relative(repoRoot, root),
      files: await walkFiles(root),
    });
  } catch (error) {
    next(error);
  }
});

app.get("/api/bugs/:project/:bugId/file", async (req, res, next) => {
  try {
    const project = sanitizeProject(req.params.project);
    const bugId = sanitizeBugId(req.params.bugId);
    const version = sanitizeVersion(req.query.version ?? "fixed");
    const root = checkoutPath(project, bugId, version);
    const relativePath = String(req.query.path ?? "");
    const filePath = safeResolve(root, relativePath);
    const stat = await fs.stat(filePath);
    if (!stat.isFile() || stat.size > 1024 * 1024) {
      throw new ApiError(400, "File is not readable in the code viewer");
    }
    res.json({
      path: relativePath,
      language: languageForFile(relativePath),
      content: await fs.readFile(filePath, "utf8"),
    });
  } catch (error) {
    next(error);
  }
});

app.get("/api/bugs/:project/:bugId/diff", async (req, res, next) => {
  try {
    const project = sanitizeProject(req.params.project);
    const bugId = sanitizeBugId(req.params.bugId);
    const buggy = checkoutPath(project, bugId, "buggy");
    const fixed = checkoutPath(project, bugId, "fixed");
    if (!(await exists(buggy)) || !(await exists(fixed))) {
      res.json({
        diff: "Checkout both buggy and fixed versions to compute a local directory diff.",
        status: "missing-checkout",
      });
      return;
    }
    const result = await runCommand(
      "diff",
      ["-ruN", "--exclude=.git", "--exclude=target", "--exclude=build", buggy, fixed],
      { allowedExitCodes: [0, 1], timeout: 120000, maxBuffer: 12 * 1024 * 1024 },
    );
    res.json({
      diff: result.stdout || "No differences reported.",
      status: result.exitCode === 1 ? "different" : "same",
    });
  } catch (error) {
    next(error);
  }
});

app.post("/api/bugs/:project/:bugId/analyze", async (req, res, next) => {
  try {
    const project = sanitizeProject(req.params.project);
    const bugId = sanitizeBugId(req.params.bugId);
    const report = analysisReportPath(project, bugId);
    if (!(await exists(report))) {
      const meta = await getBugMeta(project, bugId);
      await fs.mkdir(path.dirname(report), { recursive: true });
      const content = `# Agent 1 Report: ${project}-${bugId}

## Original Bug Metadata

- Project: ${project}
- Bug ID: ${bugId}
- Buggy revision: ${meta.buggyVersion}
- Fixed revision: ${meta.fixedVersion}
- Modified classes: ${meta.modifiedClasses.join(", ") || "unknown"}
- Triggering tests: ${meta.triggeringTests.join(", ") || "unknown"}

## Reasoning Tree TODO

- R: Regression expectation
- C: Input constraint
- D: Internal decision point
- S: State mutation
- F: Fault location
- O: Observable failure
- P: Propagation path

This placeholder was generated from local Defects4J metadata. Later agent integration can replace it with the full thesis reasoning report.
`;
      await fs.writeFile(report, content);
    }
    res.json(await getBugDetail(project, bugId));
  } catch (error) {
    next(error);
  }
});

app.post("/api/variants", async (req, res, next) => {
  try {
    const project = sanitizeProject(req.body?.project);
    const bugId = sanitizeBugId(req.body?.bugId);
    const level = sanitizeLevel(req.body?.level);
    const dimension = String(req.body?.dimension ?? "trigger-condition substitution");
    if (!Object.hasOwn(nodeForDimension, dimension)) {
      throw new ApiError(400, "Invalid variant dimension");
    }
    const candidateCount = Math.max(1, Math.min(8, Number(req.body?.candidateCount ?? 3)));
    const humanCheckpoint = Boolean(req.body?.humanCheckpoint ?? true);
    const run = await createIncompleteVariant({
      variantsRoot,
      repoRoot,
      project,
      bugId,
      level,
      dimension,
      candidateCount,
      humanCheckpoint,
    });
    res.json(run);
  } catch (error) {
    next(error);
  }
});

app.get("/api/variants", async (_, res, next) => {
  try {
    const records = await discoverVariantRecords(variantsRoot);
    res.json({
      summary: summarizeVariantRecords(records),
      groups: groupVariantRecords(records),
      variants: records.map((record) => variantRecordToDetail(record, repoRoot)),
    });
  } catch (error) {
    next(error);
  }
});

app.post("/api/variants/generate-missing-l10", async (_, res, next) => {
  try {
    const projects = await getActiveProjects();
    const results = [];
    for (const project of projects) {
      results.push(await attemptProjectL10(project, "1"));
    }
    const batch = await createBatchReport({ repoRoot, runsRoot, projects, results });
    res.json(batch);
  } catch (error) {
    next(error);
  }
});

app.post("/api/bugs/:project/1/generate-variant", async (req, res, next) => {
  try {
    const project = sanitizeProject(req.params.project);
    res.json(await attemptProjectL10(project, "1", req.body ?? {}));
  } catch (error) {
    next(error);
  }
});

app.get("/api/variants/:variantId/reasoning-tree", async (req, res, next) => {
  try {
    const record = await findCanonicalVariantRecordById(req.params.variantId);
    res.json(await readVariantArtifact(record, "reasoning_tree.yaml", "yaml"));
  } catch (error) {
    next(error);
  }
});

app.get("/api/variants/:variantId/diff", async (req, res, next) => {
  try {
    const record = await findCanonicalVariantRecordById(req.params.variantId);
    res.json(await readVariantArtifact(record, "variant.patch", "diff"));
  } catch (error) {
    next(error);
  }
});

app.get("/api/variants/:variantId/test", async (req, res, next) => {
  try {
    const record = await findCanonicalVariantRecordById(req.params.variantId);
    const artifact = await readVariantArtifact(record, "test.patch", "diff");
    res.json({ ...artifact, trigger: record.manifest.trigger });
  } catch (error) {
    next(error);
  }
});

app.get("/api/variants/:variantId/validation", async (req, res, next) => {
  try {
    const record = await findCanonicalVariantRecordById(req.params.variantId);
    const logPath = path.join(record.dir, "validation.log");
    res.json({
      validation: record.validation,
      accepted: validationGatePasses(record.validation),
      log: (await exists(logPath)) ? await fs.readFile(logPath, "utf8") : "",
    });
  } catch (error) {
    next(error);
  }
});

app.get("/api/variants/:variantId/consistency", async (req, res, next) => {
  try {
    const record = await findCanonicalVariantRecordById(req.params.variantId);
    res.json(await variantArtifactConsistency(record, { checkoutRoot }));
  } catch (error) {
    next(error);
  }
});

app.post("/api/variants/:variantId/fault-localization/run", async (req, res, next) => {
  try {
    const record = await findCanonicalVariantRecordById(req.params.variantId);
    const runId = `fl-${new Date().toISOString().replace(/[:.]/g, "-")}`;
    const provider = process.env.D4J_FL_PROVIDER ?? process.env.LLM_PROVIDER ?? "";
    const task = buildFaultLocalizationTask({ record, checkoutRoot });
    if (!provider) {
      const result = emptyFaultLocalizationResult({ record, runId, status: "provider_not_configured" });
      await writeFaultLocalizationRun({ runsRoot, record, task, result });
      res.json({
        ...result,
        provider_configured: false,
        message: "Fault-localization runner is ready, but no LLM provider is currently configured.",
        agent_visible_task: task,
      });
      return;
    }
    const result = emptyFaultLocalizationResult({ record, runId, status: "runner_not_implemented" });
    await writeFaultLocalizationRun({ runsRoot, record, task, result });
    res.json({
      ...result,
      provider_configured: true,
      message: "Fault-localization provider was detected, but the runner is not implemented yet.",
      agent_visible_task: task,
    });
  } catch (error) {
    next(error);
  }
});

app.get("/api/variants/:variantId/fault-localization/runs", async (req, res, next) => {
  try {
    const record = await findCanonicalVariantRecordById(req.params.variantId);
    const variantId = record.variantId;
    res.json(await readFaultLocalizationRuns({ runsRoot, variantId }));
  } catch (error) {
    next(error);
  }
});

app.get("/api/variants/:variantId/fault-localization/runs/:runId", async (req, res, next) => {
  try {
    const record = await findCanonicalVariantRecordById(req.params.variantId);
    const variantId = record.variantId;
    let runId;
    try {
      runId = sanitizeVariantId(req.params.runId);
    } catch (error) {
      throw new ApiError(400, error.message);
    }
    const filePath = path.join(runsRoot, "fault-localization", variantId, `${runId}.json`);
    if (!(await exists(filePath))) throw new ApiError(404, "Fault-localization run not found");
    res.json(JSON.parse(await fs.readFile(filePath, "utf8")));
  } catch (error) {
    next(error);
  }
});

app.get("/api/variants/:id", async (req, res, next) => {
  try {
    let requestedId;
    try {
      requestedId = sanitizeVariantId(req.params.id);
    } catch (error) {
      throw new ApiError(400, error.message);
    }
    const canonical = await findCanonicalVariantRecordById(requestedId, false);
    if (canonical) {
      res.json({
        ...variantRecordToDetail(canonical, repoRoot),
        run: canonicalRecordToRun(canonical, repoRoot, await exists(analysisReportPath(canonical.project, canonical.bugId))),
      });
      return;
    }
    const found = await findVariantRunById(requestedId);
    if (!found) throw new ApiError(404, "Variant run not found");
    res.json(found);
  } catch (error) {
    next(error);
  }
});

app.post("/api/workflows/:id/run-agent", async (req, res, next) => {
  try {
    let requestedId;
    try {
      requestedId = sanitizeVariantId(req.params.id);
    } catch (error) {
      throw new ApiError(400, error.message);
    }
    const canonical = await findCanonicalVariantRecordById(requestedId, false);
    if (canonical) {
      res.json(canonicalRecordToRun(canonical, repoRoot, await exists(analysisReportPath(canonical.project, canonical.bugId))));
      return;
    }
    const found = await findVariantRunLocationById(requestedId);
    if (!found) throw new ApiError(404, "Variant run not found");
    const run = await readVariantRun(found.project, found.bugId, found.level, found.runName);
    const nextArtifact = run.artifacts.find((artifact) => artifact.status !== "ready");
    if (nextArtifact) {
      const target =
        nextArtifact.name === "agent1_report.md"
          ? analysisReportPath(found.project, found.bugId)
          : path.join(found.runDir, nextArtifact.name);
      await fs.mkdir(path.dirname(target), { recursive: true });
      if (!(await exists(target))) {
        await fs.writeFile(target, placeholderArtifact(nextArtifact.name, found.project, found.bugId, run));
      }
    }

    const updated = await readVariantRun(found.project, found.bugId, found.level, found.runName);
    const metadataPath = path.join(found.runDir, "variant_run.json");
    const metadata = await readJsonIfExists(metadataPath);
    await writeJson(metadataPath, {
      ...metadata,
      validation: updated.validation,
      updatedAt: new Date().toISOString(),
    });
    res.json(await readVariantRun(found.project, found.bugId, found.level, found.runName));
  } catch (error) {
    next(error);
  }
});

async function findVariantRunById(id) {
  const location = await findVariantRunLocationById(id);
  return location ? readVariantRun(location.project, location.bugId, location.level, location.runName) : null;
}

async function findVariantRunLocationById(id) {
  if (!(await exists(variantsRoot))) return null;
  const projects = await fs.readdir(variantsRoot, { withFileTypes: true });
  for (const projectEntry of projects) {
    if (!projectEntry.isDirectory()) continue;
    const [project, bugId] = projectEntry.name.split("-");
    if (!project || !bugId) continue;
    const levels = await fs.readdir(path.join(variantsRoot, projectEntry.name), { withFileTypes: true });
    for (const levelEntry of levels) {
      if (!levelEntry.isDirectory()) continue;
      const runs = await fs.readdir(path.join(variantsRoot, projectEntry.name, levelEntry.name), { withFileTypes: true });
      for (const runEntry of runs) {
        if (!runEntry.isDirectory()) continue;
        const run = await readVariantRun(project, bugId, levelEntry.name, runEntry.name);
        if (run.id === id || run.variant_id === id) {
          return {
            project,
            bugId,
            level: levelEntry.name,
            runName: runEntry.name,
            runDir: path.join(variantsRoot, projectEntry.name, levelEntry.name, runEntry.name),
          };
        }
      }
    }
  }
  return null;
}

app.use((error, _, res, __) => {
  const status = error.status ?? 500;
  res.status(status).json({
    error: error.message || "Unexpected server error",
  });
});

ensureLayout().then(() => {
  app.listen(port, "127.0.0.1", () => {
    console.log(`D4J Variant Lab API listening at http://127.0.0.1:${port}`);
    console.log(`Repo root: ${repoRoot}`);
    console.log(`Checkout root: ${checkoutRoot}`);
  });
});
