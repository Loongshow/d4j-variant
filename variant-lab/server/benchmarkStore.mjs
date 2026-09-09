import fs from "node:fs/promises";
import path from "node:path";
import {
  topTenTextToPredictionPayload,
  trajectoryJsonl,
  writePromptArtifact,
} from "./agents/agentAdapter.mjs";
import { resolveProviderConfig } from "./agents/providerConfig.mjs";
import { exists, readJsonIfExists, safeResolve, sanitizeVariantId } from "./variantLibrary.mjs";
import { buildReasoningWorkflow } from "./reasoningWorkflow.mjs";

export const AGENT_PROFILE_SCHEMA_VERSION = "d4j-agent-profile/v1";
export const BENCHMARK_RUN_SCHEMA_VERSION = "d4j-benchmark-run/v1";
export const AGENT_TASK_SCHEMA_VERSION = "d4j-agent-visible-task/v1";
export const RANKING_SCHEMA_VERSION = "d4j-top10-ranking/v1";
export const EVALUATION_SCHEMA_VERSION = "d4j-fl-evaluation/v1";
export const CALIBRATION_SCHEMA_VERSION = "d4j-chart-depth-calibration/v1";

export const chartDepthLadderSpec = [
  {
    label: "Original",
    task_id: "Chart-1",
    task_type: "original",
    reasoning_level: "Original",
    semantic_inference_steps: 10,
    reasoning_level_status: "researcher_seeded",
    gold: "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer::getLegendItems",
  },
  {
    label: "L10",
    task_id: "CHART-1-L10-SECONDARY-02",
    task_type: "variant",
    variant_id: "CHART-1-L10-SECONDARY-02",
    reasoning_level: "L10",
    semantic_inference_steps: 11,
    reasoning_level_status: "validated",
    gold: "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer::getLegendItem",
  },
  {
    label: "L20",
    task_id: "CHART-1-L20-001",
    task_type: "variant",
    variant_id: "CHART-1-L20-001",
    reasoning_level: "L20",
    semantic_inference_steps: 18,
    reasoning_level_status: "planned",
    gold: "org.jfree.chart.plot.CategoryPlot::getIndexOf",
  },
  {
    label: "L30",
    task_id: "CHART-1-L30-001",
    task_type: "variant",
    variant_id: "CHART-1-L30-001",
    reasoning_level: "L30",
    semantic_inference_steps: 25,
    reasoning_level_status: "planned",
    gold: "org.jfree.chart.plot.CategoryPlot::getRenderer",
  },
];
export const TEST_RUNS_SCHEMA_VERSION = "d4j-test-runs/v1";

export const benchmarkArtifactFiles = [
  "run_manifest.json",
  "task.json",
  "ranking.json",
  "trajectory.jsonl",
  "commands.log",
  "test_runs.json",
  "raw_agent_output.txt",
  "evaluation.json",
  "prompt.txt",
  "prompt.json",
  "workspace_manifest.json",
  "method_catalog.json",
  "fault-localization-submission.json",
  "source_hashes_before.json",
  "source_hashes_after.json",
  "source_integrity.json",
  "reasoning_workflow.json",
  "shortcut_audit.json",
];

export const benchmarkProtocol = {
  schema_version: "d4j-benchmark-protocol/v1",
  agent_receives: [
    "Failing test identifier",
    "Failing test source",
    "Stack trace",
    "Full buggy repository access",
  ],
  agent_may: ["Search repository", "Read production source", "Read test source", "Run associated failing test(s)"],
  agent_may_not: [
    "Modify production source",
    "Modify test source",
    "Access fixed revision",
    "Access variant patch",
    "Access reasoning tree",
    "Access gold faulty methods",
    "Access generation/review reports",
    "Access Git history/fix commits",
  ],
  source_immutability: {
    production_and_test_source: "immutable",
    build_and_temp_outputs: "writable",
  },
};

export function sanitizeBenchmarkId(value, label = "id") {
  const id = String(value ?? "").trim();
  if (
    !id ||
    id.includes("..") ||
    id.includes("/") ||
    id.includes("\\") ||
    path.isAbsolute(id) ||
    !/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(id)
  ) {
    throw new Error(`Invalid ${label}`);
  }
  return id;
}

function agentsPath(benchmarkRoot) {
  return path.join(benchmarkRoot, "agents.json");
}

function statusForProfile(profile, env = process.env) {
  if (!profile.framework || !profile.provider) return "invalid";
  const providerConfig = resolveProviderConfig(profile, env);
  return providerConfig.configured ? "configured" : "not_configured";
}

export function defaultAgentProfiles(env = process.env) {
  const profiles = [
    {
      agent_id: "mini-swe-gpt56",
      framework: "mini-swe-agent",
      provider: "openai",
      model: env.D4J_OPENAI_MODEL || "",
      display_name: "mini-swe / GPT-5.6",
      defaults: { max_tool_calls: 50, max_test_runs: 5, timeout_seconds: 300 },
    },
    {
      agent_id: "mini-swe-claude",
      framework: "mini-swe-agent",
      provider: "anthropic",
      model: env.D4J_CLAUDE_MODEL || "claude",
      display_name: "mini-swe / Claude",
      defaults: { max_tool_calls: 50, max_test_runs: 5, timeout_seconds: 300 },
    },
    {
      agent_id: "mini-swe-kimi",
      framework: "mini-swe-agent",
      provider: "moonshot",
      model: env.D4J_KIMI_MODEL || "kimi",
      display_name: "mini-swe / Kimi",
      defaults: { max_tool_calls: 50, max_test_runs: 5, timeout_seconds: 300 },
    },
  ];
  return profiles.map((profile) => withProfileStatus(profile, env));
}

function withProfileStatus(profile, env = process.env) {
  const providerConfig = resolveProviderConfig(profile, env);
  return {
    schema_version: AGENT_PROFILE_SCHEMA_VERSION,
    agent_id: sanitizeBenchmarkId(profile.agent_id, "agent id"),
    framework: String(profile.framework ?? "mini-swe-agent"),
    provider: providerConfig.provider,
    model: providerConfig.model || String(profile.model ?? ""),
    display_name: String(profile.display_name ?? profile.agent_id ?? "Agent"),
    status: statusForProfile(profile, env),
    defaults: normalizeBudget(profile.defaults ?? {}),
    created_at: profile.created_at ?? new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

export function withAgentRuntimeStatus(profile, { env = process.env, adapter = null } = {}) {
  const base = withProfileStatus(profile, env);
  const providerConfig = resolveProviderConfig(base, env);
  const adapterAvailable = base.framework === "mini-swe-agent" ? Boolean(adapter?.available) : false;
  const providerReady = adapterAvailable && providerConfig.configured;
  return {
    ...base,
    model: providerConfig.model || base.model,
    status: providerReady ? "ready" : base.status === "invalid" ? "invalid" : "not_configured",
    runtime: {
      adapter_available: adapterAvailable,
      credential_configured: providerConfig.credential_configured,
      credential_source: providerConfig.credential_source,
      model_configured: providerConfig.model_configured,
      provider_ready: providerReady,
    },
    provider_config: {
      provider: providerConfig.provider,
      model: providerConfig.model,
      status: providerConfig.status,
      configured: providerConfig.configured,
      supported_by_adapter: providerConfig.supported_by_adapter,
      required_any: providerConfig.required_any,
      required_model: providerConfig.required_model,
      optional: providerConfig.optional,
      missing_environment: providerConfig.missing_environment,
      credential_configured: providerConfig.credential_configured,
      credential_source: providerConfig.credential_source,
      model_configured: providerConfig.model_configured,
      provider_ready: providerReady,
      message: providerReady
        ? "mini-swe-agent, provider credential, and model are available to the backend process."
        : providerConfig.message,
    },
  };
}

export function normalizeBudget(value = {}) {
  return {
    max_tool_calls: Math.max(1, Math.min(500, Number(value.max_tool_calls ?? 50))),
    max_test_runs: Math.max(1, Math.min(50, Number(value.max_test_runs ?? 5))),
    timeout_seconds: Math.max(30, Math.min(7200, Number(value.timeout_seconds ?? 300))),
  };
}

export async function ensureAgentProfiles(benchmarkRoot, env = process.env) {
  await fs.mkdir(benchmarkRoot, { recursive: true });
  const filePath = agentsPath(benchmarkRoot);
  if (!(await exists(filePath))) {
    await fs.writeFile(filePath, `${JSON.stringify(defaultAgentProfiles(env), null, 2)}\n`);
  }
}

export async function listAgentProfiles(benchmarkRoot, env = process.env) {
  await ensureAgentProfiles(benchmarkRoot, env);
  const parsed = JSON.parse(await fs.readFile(agentsPath(benchmarkRoot), "utf8"));
  return parsed.map((profile) => withProfileStatus(profile, env));
}

export async function saveAgentProfile(benchmarkRoot, input, env = process.env) {
  await ensureAgentProfiles(benchmarkRoot, env);
  const current = await listAgentProfiles(benchmarkRoot, env);
  const agentId = sanitizeBenchmarkId(input.agent_id || slugAgentId(input), "agent id");
  const profile = withProfileStatus(
    {
      ...input,
      agent_id: agentId,
      defaults: normalizeBudget({
        max_tool_calls: input.defaults?.max_tool_calls ?? input.max_tool_calls,
        max_test_runs: input.defaults?.max_test_runs ?? input.max_test_runs,
        timeout_seconds: input.defaults?.timeout_seconds ?? input.timeout_seconds,
      }),
      created_at: current.find((item) => item.agent_id === agentId)?.created_at,
    },
    env,
  );
  const next = [profile, ...current.filter((item) => item.agent_id !== agentId)];
  await fs.writeFile(agentsPath(benchmarkRoot), `${JSON.stringify(next, null, 2)}\n`);
  return profile;
}

function slugAgentId(input) {
  const framework = String(input.framework ?? "mini-swe-agent").replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const provider = String(input.provider ?? "provider").replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const model = String(input.model ?? "model").replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return `${framework}-${provider}-${model}`.toLowerCase();
}

export function goldMethodsForVariant(record) {
  return (record.manifest?.fault?.locations ?? [])
    .filter((location) => location.class && location.method)
    .map((location) => ({
      class: String(location.class),
      method: String(location.method),
      file: String(location.file ?? ""),
    }));
}

export function goldMethodsForOriginal(project, bugId, meta = {}) {
  if (Array.isArray(meta.goldMethods) && meta.goldMethods.length > 0) {
    return meta.goldMethods.map((method) => ({
      class: String(method.class ?? ""),
      method: String(method.method ?? ""),
      file: String(method.file ?? ""),
      evidence: String(method.evidence ?? "Verified from the local Defects4J developer patch."),
      modified_classes: meta.modifiedClasses ?? [],
    }));
  }
  if (String(project) === "Chart" && Number(bugId) === 1) {
    return [
      {
        class: "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer",
        method: "getLegendItems",
        file: "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java",
        evidence: "Chart-1 developer patch changes AbstractCategoryItemRenderer#getLegendItems around the dataset null check.",
        modified_classes: meta.modifiedClasses ?? [],
      },
    ];
  }
  return [];
}

export function buildOriginalAgentTask({ project, bugId, meta, checkoutRoot, testSource = "" }) {
  const testId = meta.triggeringTests?.[0] ?? "";
  return {
    task_id: `${project}-${bugId}`,
    task_type: "original",
    source: { project, bug_id: Number(bugId) },
    agent_visible_task: {
      schema_version: AGENT_TASK_SCHEMA_VERSION,
      task_id: `${project}-${bugId}`,
      failing_test_identifier: testId,
      failing_test_source: testSource,
      stack_trace: "",
      read_only_buggy_repository_path: path.join(checkoutRoot, `${project}-${bugId}`, "buggy"),
      allowed_test_command: testId ? `defects4j test -t ${testId}` : "",
      source_immutability: benchmarkProtocol.source_immutability,
    },
    gold_methods: goldMethodsForOriginal(project, bugId, meta),
  };
}

export function buildVariantAgentTask({ record, checkoutRoot }) {
  const manifest = record.manifest;
  const source = manifest.source;
  const trigger = manifest.trigger ?? {};
  return {
    task_id: record.variantId,
    task_type: "variant",
    source: {
      project: source.defects4j_project,
      bug_id: Number(source.defects4j_bug_id),
      variant_id: record.variantId,
    },
    agent_visible_task: {
      schema_version: AGENT_TASK_SCHEMA_VERSION,
      task_id: record.variantId,
      failing_test_identifier: trigger.test_id ?? "",
      failing_test_source: trigger.source ?? "",
      stack_trace: trigger.stack_trace ?? "",
      read_only_buggy_repository_path: path.join(
        checkoutRoot,
        `${source.defects4j_project}-${source.defects4j_bug_id}`,
        "variant",
      ),
      allowed_test_command: trigger.test_id ? `defects4j test -t ${trigger.test_id}` : "",
      source_immutability: benchmarkProtocol.source_immutability,
    },
    gold_methods: goldMethodsForVariant(record),
    private_adapter: {
      variant_dir: record.dir,
      source_project: source.defects4j_project,
      source_bug_id: Number(source.defects4j_bug_id),
    },
  };
}

export function assertAgentTaskIsolation(task) {
  const serialized = JSON.stringify(task);
  const banned = [
    /fixed repository/i,
    /fixed_revision/i,
    /variant\.patch/i,
    /test\.patch/i,
    /reasoning_tree/i,
    /gold/i,
    /validation\.log/i,
    /variant_report/i,
    /candidate/i,
    /review/i,
    /\.git/i,
  ];
  const failures = banned.filter((pattern) => pattern.test(serialized)).map((pattern) => String(pattern));
  return { ok: failures.length === 0, failures };
}

export function parseTopTenRanking(input, methodCatalog = null) {
  const payload = typeof input === "string" ? JSON.parse(input) : input;
  const predictions = payload?.predictions;
  const errors = [];
  if (!Array.isArray(predictions)) {
    return { ok: false, predictions: [], errors: ["predictions must be an array"] };
  }
  if (predictions.length !== 10) errors.push("exactly 10 predictions are required");
  const seen = new Set();
  const normalized = predictions.map((prediction, index) => {
    const rank = Number(prediction.rank ?? index + 1);
    const className = String(prediction.class ?? "");
    const method = String(prediction.method ?? "");
    const key = `${className}::${method}`;
    if (rank !== index + 1) errors.push(`rank ${index + 1} is missing or out of order`);
    if (!className || !method) errors.push(`rank ${index + 1} is missing class or method`);
    if (seen.has(key)) errors.push(`duplicate prediction: ${key}`);
    seen.add(key);
    if (/(\.|^)tests?\.|Test$|Tests$|^test/.test(className) || /^test[A-Z0-9_]/.test(method)) {
      errors.push(`test method prediction is not allowed: ${key}`);
    }
    if (methodCatalog && !methodCatalog.has(key)) {
      errors.push(`nonexistent method: ${key}`);
    }
    return { rank, class: className, method };
  });
  return { ok: errors.length === 0, predictions: normalized, errors };
}

export function evaluateRanking(predictions, goldMethods) {
  if (!Array.isArray(goldMethods) || goldMethods.length === 0) {
    return {
      schema_version: EVALUATION_SCHEMA_VERSION,
      gold_methods: [],
      gold_rank: null,
      hit_at_5: null,
      hit_at_10: null,
      status: "no_gold_metadata",
    };
  }
  const goldKeys = new Set(goldMethods.map((method) => `${method.class}::${method.method}`));
  const hit = predictions.find((prediction) => goldKeys.has(`${prediction.class}::${prediction.method}`));
  const goldRank = hit?.rank ?? null;
  return {
    schema_version: EVALUATION_SCHEMA_VERSION,
    gold_methods: goldMethods,
    gold_rank: goldRank,
    hit_at_5: goldRank == null ? false : goldRank <= 5,
    hit_at_10: goldRank == null ? false : goldRank <= 10,
    status: "evaluated",
  };
}

export function computeBehaviorMetrics(events = [], goldMethods = []) {
  const fileReads = new Map();
  let toolCallCount = 0;
  let searchCount = 0;
  let testRunCount = 0;
  for (const event of events) {
    toolCallCount += 1;
    if (event.type === "search") searchCount += 1;
    if (event.type === "test_run") testRunCount += 1;
    if (event.type === "open_file") {
      const target = String(event.target ?? "");
      const current = fileReads.get(target) ?? {
        file: target,
        type: /(^|\/)tests?\//.test(target) || /Test\.java$/.test(target) ? "test" : "production",
        read_count: 0,
        first_read_position: event.sequence ?? toolCallCount,
      };
      current.read_count += 1;
      fileReads.set(target, current);
    }
  }
  const files = Array.from(fileReads.values()).sort((a, b) => a.first_read_position - b.first_read_position);
  const goldFiles = new Set(goldMethods.map((method) => method.file).filter(Boolean));
  for (const file of files) {
    file.contains_gold_method = goldFiles.has(file.file);
  }
  const firstGold = files.find((file) => file.contains_gold_method);
  return {
    tool_call_count: toolCallCount,
    search_count: searchCount,
    file_read_count: files.reduce((total, file) => total + file.read_count, 0),
    unique_files_read: files.length,
    production_files_read: files.filter((file) => file.type === "production").length,
    test_files_read: files.filter((file) => file.type === "test").length,
    test_run_count: testRunCount,
    gold_file_read: Boolean(firstGold),
    first_gold_file_read_position: firstGold?.first_read_position ?? null,
    files,
  };
}

export function parseBenchmarkDurationMs(commands = "") {
  const matches = Array.from(String(commands ?? "").matchAll(/^duration_ms:\s*(\d+)\s*$/gm));
  if (!matches.length) return null;
  const value = Number(matches.at(-1)?.[1]);
  return Number.isFinite(value) ? value : null;
}

export function fileOverlap(filesA = [], filesB = []) {
  const setA = new Set(filesA);
  const setB = new Set(filesB);
  const union = new Set([...setA, ...setB]);
  const intersection = [...setA].filter((file) => setB.has(file));
  return {
    jaccard: union.size === 0 ? null : intersection.length / union.size,
    shared_files: intersection,
    only_a: [...setA].filter((file) => !setB.has(file)),
    only_b: [...setB].filter((file) => !setA.has(file)),
    intersection_count: intersection.length,
    union_count: union.size,
  };
}

function benchmarkRunRoot(benchmarkRoot, agentId, taskId) {
  return path.join(benchmarkRoot, sanitizeBenchmarkId(agentId, "agent id"), sanitizeBenchmarkId(taskId, "task id"));
}

async function nextRunId(taskRoot) {
  await fs.mkdir(taskRoot, { recursive: true });
  for (let index = 1; index < 1000; index += 1) {
    const runId = `run-${String(index).padStart(3, "0")}`;
    if (!(await exists(path.join(taskRoot, runId)))) return runId;
  }
  throw new Error("No available benchmark run id below run-1000");
}

export async function createBenchmarkRun({ benchmarkRoot, repoRoot, agent, taskBundle, budget, repeat_index = 1, adapter = null }) {
  const agentId = sanitizeBenchmarkId(agent.agent_id, "agent id");
  const taskId = sanitizeBenchmarkId(taskBundle.task_id, "task id");
  const taskRoot = benchmarkRunRoot(benchmarkRoot, agentId, taskId);
  const runId = await nextRunId(taskRoot);
  const runDir = path.join(taskRoot, runId);
  await fs.mkdir(runDir, { recursive: false });

  const now = new Date().toISOString();
  const globalRunId = `${agentId}__${taskId}__${runId}`;
  const budgetConfig = normalizeBudget(budget ?? agent.defaults);
  let prepared = null;
  let taskForAgent = taskBundle.agent_visible_task;
  let renderedPrompt = "";
  let prompt = null;
  const agentRuntimeConfigured = agent.status === "ready" || agent.status === "configured";
  let execution = {
    status: agentRuntimeConfigured ? "agent_not_installed" : "provider_not_configured",
    status_reason: agentRuntimeConfigured ? "No agent adapter was provided for this run." : "Provider is not configured in the backend environment.",
    provider_config: null,
    adapter: null,
    raw_output: "",
    commands: "",
    trajectory: [],
    test_runs: [],
    ranking_text: "",
    ranking_payload: null,
    structured_submission: null,
  };
  let sourceIntegrity = {
    ok: true,
    changed_files: [],
    before_file_count: 0,
    after_file_count: 0,
    checked_at: now,
  };
  let sourceHashesAfter = {
    schema_version: "d4j-source-hashes/v1",
    file_count: 0,
    aggregate_sha256: "",
    files: [],
    generated_at: now,
  };
  let setupError = "";

  try {
    const initialIsolation = assertAgentTaskIsolation(taskForAgent);
    if (!initialIsolation.ok) {
      throw new Error(`Agent-visible task leaks benchmark metadata before preparation: ${initialIsolation.failures.join(", ")}`);
    }

    if (adapter) {
      prepared = await adapter.prepareRun({ runDir, taskBundle, agent, budget: budgetConfig });
      taskForAgent = prepared.agent_visible_task;
      if (prepared.workspace_manifest?.private_metadata_scan && !prepared.workspace_manifest.private_metadata_scan.ok) {
        throw new Error(
          `Agent workspace isolation failed: ${prepared.workspace_manifest.private_metadata_scan.banned_entries.join(", ")}`,
        );
      }
    }

    const preparedIsolation = assertAgentTaskIsolation(taskForAgent);
    if (!preparedIsolation.ok) {
      throw new Error(`Agent-visible task leaks benchmark metadata after preparation: ${preparedIsolation.failures.join(", ")}`);
    }

    prompt = await writePromptArtifact(runDir, taskForAgent);
    renderedPrompt = prompt.rendered;

    if (adapter) {
      execution = await adapter.execute({
        runDir,
        agent,
        budget: budgetConfig,
        prepared,
        renderedPrompt,
      });
    }

    if (prepared && adapter?.collectSourceIntegrity) {
      const integrity = await adapter.collectSourceIntegrity(prepared);
      sourceIntegrity = integrity.comparison;
      sourceHashesAfter = integrity.after;
    }
  } catch (error) {
    setupError = error instanceof Error ? error.message : "Unknown benchmark setup error";
    execution = {
      ...execution,
      status: "failed",
      status_reason: setupError,
    };
    if (!prompt) {
      prompt = await writePromptArtifact(runDir, taskForAgent);
      renderedPrompt = prompt.rendered;
    }
  }

  const parseableRankingPayload =
    execution.status === "completed" && execution.ranking_payload
      ? execution.ranking_payload
      : execution.status === "completed" && execution.ranking_text
        ? topTenTextToPredictionPayload(execution.ranking_text)
        : null;
  const parsedRanking = parseableRankingPayload
    ? parseTopTenRanking(parseableRankingPayload, prepared?.method_catalog ?? null)
    : { ok: false, predictions: [], errors: execution.status === "completed" ? ["unparseable result"] : [] };
  let status = execution.status;
  let statusReason = execution.status_reason;
  if (status === "completed" && !parsedRanking.ok) {
    status = "invalid_ranking";
    statusReason = `Top-10 output invalid: ${parsedRanking.errors.join("; ") || "unparseable result"}`;
  }
  if (prepared?.workspace_manifest?.private_metadata_scan && !prepared.workspace_manifest.private_metadata_scan.ok) {
    status = "protocol_violation";
    statusReason = "Agent-visible workspace contains private benchmark metadata.";
  }
  if (!sourceIntegrity.ok) {
    status = "protocol_violation";
    statusReason = "Production/test source changed during the localization run.";
  }

  const ranking = {
    schema_version: RANKING_SCHEMA_VERSION,
    run_id: globalRunId,
    status,
    parse_status: parseableRankingPayload ? (parsedRanking.ok ? "parsed" : "invalid") : "not_run",
    source: execution.structured_submission?.ok ? "structured_submit_fault_localization" : "none",
    structured_submission: execution.structured_submission ?? null,
    predictions: parsedRanking.predictions,
    validation_errors: parsedRanking.errors,
  };
  const evaluatedRanking = evaluateRanking(ranking.predictions, taskBundle.gold_methods);
  const evaluation = {
    ...evaluatedRanking,
    run_id: globalRunId,
    gold_rank: status === "completed" ? evaluatedRanking.gold_rank : null,
    hit_at_5: status === "completed" ? evaluatedRanking.hit_at_5 : null,
    hit_at_10: status === "completed" ? evaluatedRanking.hit_at_10 : null,
    status,
    status_reason: statusReason,
  };
  const metrics = computeBehaviorMetrics(execution.trajectory ?? [], taskBundle.gold_methods);
  const reasoningWorkflow = buildReasoningWorkflow({
    runId: globalRunId,
    trajectory: execution.trajectory ?? [],
    structuredSubmission: execution.structured_submission ?? null,
    createdAt: now,
  });
  const manifest = {
    schema_version: BENCHMARK_RUN_SCHEMA_VERSION,
    id: globalRunId,
    run_id: runId,
    task_id: taskId,
    task_type: taskBundle.task_type,
    source: taskBundle.source,
    agent: {
      agent_id: agent.agent_id,
      framework: agent.framework,
      provider: agent.provider,
      model: agent.model,
      display_name: agent.display_name,
    },
    budget: budgetConfig,
    repeats: { repeat_index },
    protocol: benchmarkProtocol,
    prompt: prompt?.metadata ?? null,
    provider_config: execution.provider_config ?? null,
    adapter: execution.adapter ?? null,
    timeouts: {
      agent_startup_seconds: execution.timeouts?.agent_startup_seconds ?? null,
      benchmark_execution_seconds: execution.timeouts?.benchmark_execution_seconds ?? budgetConfig.timeout_seconds,
      execution_timer_starts:
        execution.timeouts?.execution_timer_starts ?? "after adapter starts the fault-localization task",
    },
    workspace: prepared?.workspace_manifest ?? null,
    isolation: {
      agent_task: assertAgentTaskIsolation(taskForAgent),
      fixed_code_inaccessible: prepared?.isolation?.fixed_code_inaccessible ?? false,
      git_history_inaccessible: prepared?.isolation?.git_history_inaccessible ?? false,
      private_metadata_inaccessible: prepared?.isolation?.private_metadata_inaccessible ?? false,
      scan: prepared?.isolation?.scan ?? null,
    },
    integrity: sourceIntegrity,
    status,
    status_reason: statusReason,
    metrics,
    artifact_path: `${path.relative(repoRoot, runDir)}/`,
    started_at: now,
    completed_at: now,
  };

  await fs.writeFile(path.join(runDir, "run_manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  await fs.writeFile(path.join(runDir, "task.json"), `${JSON.stringify(taskForAgent, null, 2)}\n`);
  await fs.writeFile(path.join(runDir, "ranking.json"), `${JSON.stringify(ranking, null, 2)}\n`);
  await fs.writeFile(path.join(runDir, "trajectory.jsonl"), trajectoryJsonl(execution.trajectory ?? []));
  await fs.writeFile(path.join(runDir, "commands.log"), execution.commands ?? "");
  await fs.writeFile(
    path.join(runDir, "test_runs.json"),
    `${JSON.stringify({ schema_version: TEST_RUNS_SCHEMA_VERSION, run_id: globalRunId, test_runs: execution.test_runs ?? [] }, null, 2)}\n`,
  );
  await fs.writeFile(path.join(runDir, "raw_agent_output.txt"), execution.raw_output ?? "");
  await fs.writeFile(path.join(runDir, "evaluation.json"), `${JSON.stringify(evaluation, null, 2)}\n`);
  await fs.writeFile(path.join(runDir, "source_hashes_after.json"), `${JSON.stringify(sourceHashesAfter, null, 2)}\n`);
  await fs.writeFile(path.join(runDir, "source_integrity.json"), `${JSON.stringify(sourceIntegrity, null, 2)}\n`);
  await fs.writeFile(path.join(runDir, "reasoning_workflow.json"), `${JSON.stringify(reasoningWorkflow, null, 2)}\n`);
  if (!(await exists(path.join(runDir, "workspace_manifest.json")))) {
    await fs.writeFile(
      path.join(runDir, "workspace_manifest.json"),
      `${JSON.stringify(
        {
          schema_version: "d4j-agent-workspace/v1",
          status: adapter ? "not_prepared" : "adapter_missing",
          setup_error: setupError,
        },
        null,
        2,
      )}\n`,
    );
  }
  if (!(await exists(path.join(runDir, "source_hashes_before.json")))) {
    await fs.writeFile(
      path.join(runDir, "source_hashes_before.json"),
      `${JSON.stringify(
        {
          schema_version: "d4j-source-hashes/v1",
          file_count: 0,
          aggregate_sha256: "",
          files: [],
          generated_at: now,
        },
        null,
        2,
      )}\n`,
    );
  }

  return readBenchmarkRunDetail(runDir, repoRoot);
}

export async function discoverBenchmarkRunRecords(benchmarkRoot, repoRoot) {
  if (!(await exists(benchmarkRoot))) return [];
  const records = [];
  const agentEntries = await fs.readdir(benchmarkRoot, { withFileTypes: true });
  for (const agentEntry of agentEntries) {
    if (!agentEntry.isDirectory()) continue;
    try {
      sanitizeBenchmarkId(agentEntry.name, "agent id");
    } catch {
      continue;
    }
    const agentRoot = path.join(benchmarkRoot, agentEntry.name);
    const taskEntries = await fs.readdir(agentRoot, { withFileTypes: true }).catch(() => []);
    for (const taskEntry of taskEntries) {
      if (!taskEntry.isDirectory()) continue;
      try {
        sanitizeBenchmarkId(taskEntry.name, "task id");
      } catch {
        continue;
      }
      const taskRoot = path.join(agentRoot, taskEntry.name);
      const runEntries = await fs.readdir(taskRoot, { withFileTypes: true }).catch(() => []);
      for (const runEntry of runEntries) {
        if (!runEntry.isDirectory() || !/^run-\d{3}$/.test(runEntry.name)) continue;
        const detail = await readBenchmarkRunDetail(path.join(taskRoot, runEntry.name), repoRoot).catch(() => null);
        if (detail) records.push(detail);
      }
    }
  }
  return records.sort((a, b) => String(b.manifest.started_at).localeCompare(String(a.manifest.started_at)));
}

export async function readBenchmarkRunDetail(runDir, repoRoot) {
  const manifest = JSON.parse(await fs.readFile(path.join(runDir, "run_manifest.json"), "utf8"));
  const task = JSON.parse(await fs.readFile(path.join(runDir, "task.json"), "utf8"));
  const ranking = JSON.parse(await fs.readFile(path.join(runDir, "ranking.json"), "utf8"));
  const evaluation = JSON.parse(await fs.readFile(path.join(runDir, "evaluation.json"), "utf8"));
  const testRuns = JSON.parse(await fs.readFile(path.join(runDir, "test_runs.json"), "utf8"));
  const trajectoryText = await fs.readFile(path.join(runDir, "trajectory.jsonl"), "utf8");
  const trajectory = trajectoryText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const commands = await fs.readFile(path.join(runDir, "commands.log"), "utf8");
  const raw_output = await fs.readFile(path.join(runDir, "raw_agent_output.txt"), "utf8");
  const reasoningWorkflowPath = path.join(runDir, "reasoning_workflow.json");
  let reasoning_workflow = await readJsonIfExists(reasoningWorkflowPath);
  if (!reasoning_workflow) {
    reasoning_workflow = buildReasoningWorkflow({
      runId: manifest.id,
      trajectory,
      structuredSubmission: ranking.structured_submission ?? null,
      createdAt: manifest.started_at,
    });
    await fs.writeFile(reasoningWorkflowPath, `${JSON.stringify(reasoning_workflow, null, 2)}\n`);
  }
  reasoning_workflow = {
    ...reasoning_workflow,
    nodes: (reasoning_workflow.nodes ?? []).map((node) => ({
      ...node,
      event_type: node.event_type ?? node.kind,
      file: node.file ?? node.references?.[0]?.file ?? (node.kind === "file_read" ? node.evidence || null : null),
      command: node.command ?? (["search", "test_run", "evidence"].includes(node.kind) ? node.evidence || null : node.kind === "final_submission" ? "submit_fault_localization" : null),
    })),
  };
  const shortcut_audit = await readJsonIfExists(path.join(runDir, "shortcut_audit.json"));
  return {
    id: manifest.id,
    run_dir: runDir,
    artifact_path: `${path.relative(repoRoot, runDir)}/`,
    manifest,
    task,
    ranking,
    trajectory,
    commands,
    test_runs: testRuns.test_runs ?? [],
    raw_output,
    evaluation,
    reasoning_workflow,
    shortcut_audit,
    files: manifest.metrics?.files ?? [],
  };
}

export async function findBenchmarkRunById(benchmarkRoot, repoRoot, id, throwIfMissing = true) {
  let runId;
  try {
    runId = sanitizeBenchmarkId(id, "run id");
  } catch (error) {
    if (!throwIfMissing) return null;
    throw error;
  }
  const records = await discoverBenchmarkRunRecords(benchmarkRoot, repoRoot);
  const found = records.find((record) => record.id === runId || record.manifest.id === runId);
  if (!found && throwIfMissing) throw new Error("Benchmark run not found");
  return found ?? null;
}

export function summarizeBenchmarkRuns(records) {
  const statusCounts = {};
  for (const record of records) {
    const status = record.manifest.status;
    statusCounts[status] = (statusCounts[status] ?? 0) + 1;
  }
  return { total: records.length, statuses: statusCounts };
}

export function groupBenchmarkRuns(records) {
  const agentMap = new Map();
  for (const record of records) {
    const agentId = record.manifest.agent.agent_id;
    if (!agentMap.has(agentId)) {
      agentMap.set(agentId, {
        agent_id: agentId,
        display_name: record.manifest.agent.display_name,
        tasks: new Map(),
      });
    }
    const agent = agentMap.get(agentId);
    const taskId = record.manifest.task_id;
    if (!agent.tasks.has(taskId)) {
      agent.tasks.set(taskId, { task_id: taskId, task_type: record.manifest.task_type, runs: [] });
    }
    agent.tasks.get(taskId).runs.push(recordToRunSummary(record));
  }
  return Array.from(agentMap.values()).map((agent) => ({
    agent_id: agent.agent_id,
    display_name: agent.display_name,
    tasks: Array.from(agent.tasks.values()).map((task) => ({
      ...task,
      runs: task.runs.sort((a, b) => b.run_id.localeCompare(a.run_id)),
    })),
  }));
}

export function recordToRunSummary(record) {
  return {
    id: record.id,
    run_id: record.manifest.run_id,
    task_id: record.manifest.task_id,
    task_type: record.manifest.task_type,
    agent_id: record.manifest.agent.agent_id,
    agent_display_name: record.manifest.agent.display_name,
    model: record.manifest.agent.model,
    status: record.manifest.status,
    gold_rank: record.evaluation.gold_rank,
    hit_at_5: record.evaluation.hit_at_5,
    hit_at_10: record.evaluation.hit_at_10,
    tool_call_count: record.manifest.metrics?.tool_call_count ?? null,
    unique_files_read: record.manifest.metrics?.unique_files_read ?? null,
    test_run_count: record.manifest.metrics?.test_run_count ?? null,
    duration_ms: parseBenchmarkDurationMs(record.commands),
    artifact_path: record.artifact_path,
    started_at: record.manifest.started_at,
    completed_at: record.manifest.completed_at,
  };
}

export async function readBenchmarkArtifact(record, artifactName) {
  if (!benchmarkArtifactFiles.includes(artifactName)) throw new Error("Invalid benchmark artifact");
  const filePath = safeResolve(record.run_dir, artifactName);
  if (!(await exists(filePath))) throw new Error(`${artifactName} not found`);
  if (artifactName.endsWith(".json")) return JSON.parse(await fs.readFile(filePath, "utf8"));
  return await fs.readFile(filePath, "utf8");
}

export function compareOriginalVariantRuns(originalRun, variantRun) {
  const metrics = [
    ["Gold Rank", originalRun.evaluation.gold_rank, variantRun.evaluation.gold_rank],
    ["Hit@5", originalRun.evaluation.hit_at_5, variantRun.evaluation.hit_at_5],
    ["Hit@10", originalRun.evaluation.hit_at_10, variantRun.evaluation.hit_at_10],
    ["Tool Calls", originalRun.manifest.metrics?.tool_call_count ?? 0, variantRun.manifest.metrics?.tool_call_count ?? 0],
    ["Searches", originalRun.manifest.metrics?.search_count ?? 0, variantRun.manifest.metrics?.search_count ?? 0],
    ["Files Read", originalRun.manifest.metrics?.file_read_count ?? 0, variantRun.manifest.metrics?.file_read_count ?? 0],
    ["Unique Files Read", originalRun.manifest.metrics?.unique_files_read ?? 0, variantRun.manifest.metrics?.unique_files_read ?? 0],
    ["Test Runs", originalRun.manifest.metrics?.test_run_count ?? 0, variantRun.manifest.metrics?.test_run_count ?? 0],
    ["Duration", parseBenchmarkDurationMs(originalRun.commands), parseBenchmarkDurationMs(variantRun.commands)],
    [
      "Gold File Read Position",
      originalRun.manifest.metrics?.first_gold_file_read_position ?? null,
      variantRun.manifest.metrics?.first_gold_file_read_position ?? null,
    ],
  ];
  const overlap = fileOverlap(
    (originalRun.files ?? []).map((file) => file.file),
    (variantRun.files ?? []).map((file) => file.file),
  );
  return {
    mode: "original_vs_variant",
    original_run_id: originalRun.id,
    variant_run_id: variantRun.id,
    rows: metrics.map(([metric, original, variant]) => ({ metric, original, variant })),
    file_overlap: overlap,
  };
}

function runSortKey(record) {
  const runId = String(record.manifest?.run_id ?? "");
  const numeric = Number(runId.match(/run-(\d+)/)?.[1] ?? 0);
  return {
    started_at: String(record.manifest?.started_at ?? ""),
    run_number: Number.isFinite(numeric) ? numeric : 0,
  };
}

function compareRunsDescending(a, b) {
  const ak = runSortKey(a);
  const bk = runSortKey(b);
  const byStarted = bk.started_at.localeCompare(ak.started_at);
  if (byStarted) return byStarted;
  return bk.run_number - ak.run_number;
}

function selectDepthRun(records, taskId) {
  const matching = records.filter((record) => record.manifest?.task_id === taskId).sort(compareRunsDescending);
  return matching.find((record) => record.manifest?.status === "completed") ?? matching[0] ?? null;
}

function variantReasoningMetadata(variantRecords, spec) {
  const record = variantRecords.find((item) => item.variantId === spec.variant_id || item.manifest?.variant_id === spec.variant_id);
  const reasoning = record?.manifest?.reasoning ?? {};
  const steps = Number(
    reasoning.semantic_inference_steps ?? reasoning.unit_count ?? reasoning.path_length ?? spec.semantic_inference_steps,
  );
  return {
    semantic_inference_steps: Number.isFinite(steps) ? steps : spec.semantic_inference_steps,
    reasoning_level: String(reasoning.level ?? spec.reasoning_level),
    reasoning_level_status: String(
      reasoning.reasoning_level_status ?? record?.manifest?.reproducibility?.status ?? spec.reasoning_level_status,
    ),
    variant_status: record?.status ?? (spec.variant_id ? "not_generated" : "baseline"),
    benchmark_eligible: record ? Boolean(record.manifest?.benchmark_eligible) : false,
  };
}

function depthRowFor(spec, run, variantRecords) {
  const metadata = spec.task_type === "variant" ? variantReasoningMetadata(variantRecords, spec) : spec;
  const metrics = run?.manifest?.metrics ?? {};
  const status = run?.manifest?.status ?? (metadata.variant_status === "not_generated" ? "not_generated" : "not_run");
  return {
    label: spec.label,
    task: spec.task_id,
    task_id: spec.task_id,
    task_type: spec.task_type,
    variant_id: spec.variant_id ?? null,
    reasoning_level: metadata.reasoning_level,
    semantic_inference_steps: metadata.semantic_inference_steps,
    reasoning_level_status: metadata.reasoning_level_status,
    variant_status: metadata.variant_status ?? "baseline",
    benchmark_eligible: metadata.benchmark_eligible ?? true,
    run_id: run?.id ?? null,
    run_number: run?.manifest?.run_id ?? null,
    status,
    artifact_path: run?.artifact_path ?? null,
    model: run?.manifest?.agent?.model ?? null,
    gold_method: spec.gold,
    gold_rank: status === "completed" ? run?.evaluation?.gold_rank ?? null : null,
    hit_at_5: status === "completed" ? run?.evaluation?.hit_at_5 ?? null : null,
    hit_at_10: status === "completed" ? run?.evaluation?.hit_at_10 ?? null : null,
    tool_calls: metrics.tool_call_count ?? null,
    searches: metrics.search_count ?? null,
    files_read: metrics.file_read_count ?? null,
    unique_files_read: metrics.unique_files_read ?? null,
    production_files_read: metrics.production_files_read ?? null,
    test_files_read: metrics.test_files_read ?? null,
    test_runs: metrics.test_run_count ?? null,
    duration_ms: run ? parseBenchmarkDurationMs(run.commands) : null,
    first_gold_file_position: metrics.first_gold_file_read_position ?? null,
    gold_file_read: metrics.gold_file_read ?? null,
    files: run?.files ?? [],
  };
}

export function buildFileOverlapMatrix(depthRows) {
  const labels = depthRows.map((row) => row.label);
  const matrix = labels.map((from) =>
    labels.map((to) => ({
      from,
      to,
      jaccard: from === to ? 1 : null,
    })),
  );
  const pairs = [];
  for (let i = 0; i < depthRows.length; i += 1) {
    for (let j = 0; j < depthRows.length; j += 1) {
      if (i === j) continue;
      const first = depthRows[i];
      const second = depthRows[j];
      if (first.status !== "completed" || second.status !== "completed") continue;
      const overlap = fileOverlap(
        (first.files ?? []).map((file) => file.file),
        (second.files ?? []).map((file) => file.file),
      );
      matrix[i][j] = { from: first.label, to: second.label, jaccard: overlap.jaccard };
      if (i < j) {
        pairs.push({
          from: first.label,
          to: second.label,
          ...overlap,
        });
      }
    }
  }
  return { labels, matrix, pairs };
}

export function buildChartDepthLadder(records, variantRecords = []) {
  const rows = chartDepthLadderSpec.map((spec) => depthRowFor(spec, selectDepthRun(records, spec.task_id), variantRecords));
  const completedRows = rows.filter((row) => row.status === "completed");
  return {
    schema_version: CALIBRATION_SCHEMA_VERSION,
    title: "Chart-1 GPT-5.6 Calibration Pilot",
    scope: "PILOT: n=1 original and n=1 per completed variant; not final benchmark accuracy.",
    frozen_protocol: benchmarkProtocol,
    rows,
    pilot_baseline: {
      original: rows.find((row) => row.label === "Original") ?? null,
      l10: rows.find((row) => row.label === "L10") ?? null,
      file_jaccard:
        completedRows.some((row) => row.label === "Original") && completedRows.some((row) => row.label === "L10")
          ? fileOverlap(
              (rows.find((row) => row.label === "Original")?.files ?? []).map((file) => file.file),
              (rows.find((row) => row.label === "L10")?.files ?? []).map((file) => file.file),
            ).jaccard
          : null,
    },
    file_overlap_matrix: buildFileOverlapMatrix(rows),
    generated_at: new Date().toISOString(),
  };
}

export function compareAgentRuns(runs) {
  const rows = runs.map((run) => ({
    agent: run.manifest.agent.display_name,
    run_id: run.id,
    gold_rank: run.evaluation.gold_rank,
    hit_at_5: run.evaluation.hit_at_5,
    hit_at_10: run.evaluation.hit_at_10,
    files_read: run.manifest.metrics?.file_read_count ?? 0,
    tool_calls: run.manifest.metrics?.tool_call_count ?? 0,
  }));
  const overlaps = [];
  for (let i = 0; i < runs.length; i += 1) {
    for (let j = i + 1; j < runs.length; j += 1) {
      const first = runs[i];
      const second = runs[j];
      overlaps.push({
        pair: `${first.manifest.agent.display_name} <-> ${second.manifest.agent.display_name}`,
        ...fileOverlap(
          (first.files ?? []).map((file) => file.file),
          (second.files ?? []).map((file) => file.file),
        ),
      });
    }
  }
  return { mode: "agent_vs_agent", rows, overlaps };
}

export function matchingPairForRun(run, records) {
  const source = run.manifest.source ?? {};
  if (run.manifest.task_type === "original") {
    return records.find(
      (candidate) =>
        candidate.manifest.task_type === "variant" &&
        candidate.manifest.agent.agent_id === run.manifest.agent.agent_id &&
        candidate.manifest.source?.project === source.project &&
        Number(candidate.manifest.source?.bug_id) === Number(source.bug_id),
    );
  }
  if (run.manifest.task_type === "variant") {
    return records.find(
      (candidate) =>
        candidate.manifest.task_type === "original" &&
        candidate.manifest.agent.agent_id === run.manifest.agent.agent_id &&
        candidate.manifest.source?.project === source.project &&
        Number(candidate.manifest.source?.bug_id) === Number(source.bug_id),
    );
  }
  return null;
}

export function assertNoCredentialFields(profile) {
  const serialized = JSON.stringify(profile);
  return !/(api[_-]?key|secret|token|password)/i.test(serialized);
}
