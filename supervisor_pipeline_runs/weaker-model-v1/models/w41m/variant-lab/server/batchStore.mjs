import fs from "node:fs/promises";
import path from "node:path";
import { exists, safeResolve } from "./variantLibrary.mjs";

export const BATCH_SCHEMA_VERSION = "d4j-controlled-reasoning-batch/v1";
export const DEFAULT_BATCH_ID = "multi-family-l10-l30-l50-v1";
export const MULTI_FAMILY_PROJECTS = ["Cli", "Collections", "Math", "Lang", "Csv", "Codec", "Gson", "Time", "Closure"];
export const MULTI_FAMILY_LEVELS = ["L10", "L30", "L50"];
export const DEPTH_LADDER_BATCH_ID = "seven-family-l10-l90-v1";
export const DEPTH_LADDER_PROJECTS = ["Chart", "Math", "Codec", "Closure", "Cli", "Collections", "Csv"];
export const DEPTH_LADDER_LEVELS = ["L10", "L30", "L50", "L70", "L90"];

const terminalVariantStatuses = new Set([
  "validated",
  "depth_unachievable",
  "generation_failed",
  "candidate_rejected",
  "validation_failed",
  "reproducibility_failed",
  "environment_blocked",
  "benchmark_ineligible",
  "not_attempted_due_to_dependency",
]);

const terminalBenchmarkStatuses = new Set([
  "completed",
  "timeout",
  "provider_error",
  "agent_protocol_error",
  "invalid_ranking",
  "protocol_violation",
  "failed",
]);

function safeBatchId(value) {
  const batchId = String(value ?? "").trim();
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(batchId) || batchId.includes("..")) {
    throw new Error("Invalid batch id");
  }
  return batchId;
}

export function batchDirectory(benchmarkRoot, batchId = DEFAULT_BATCH_ID) {
  return safeResolve(path.join(benchmarkRoot, "batches"), safeBatchId(batchId));
}

function nowIso() {
  return new Date().toISOString();
}

function originalEntry(project, timestamp) {
  return {
    key: `${project}-1:Original`,
    task_kind: "original",
    project,
    bug: 1,
    level: "Original",
    current_stage: "verify_original",
    status: "pending",
    started_at: null,
    updated_at: timestamp,
    artifact_paths: [],
    failure_reason: null,
    resume_from: "verify_original",
    benchmark_status: "not_run",
    benchmark_run_id: null,
  };
}

function variantEntry(project, level, timestamp) {
  return {
    key: `${project}-1:${level}`,
    task_kind: "private_variant",
    project,
    bug: 1,
    level,
    current_stage: "waiting_for_original",
    status: "pending",
    started_at: null,
    updated_at: timestamp,
    artifact_paths: [],
    failure_reason: null,
    resume_from: "waiting_for_original",
    variant_id: null,
    reasoning_level: level,
    semantic_inference_steps: null,
    shortest_reasoning_path: [],
    shortcut_risks: [],
    reasoning_level_status: "not_assessed",
    benchmark_status: "not_run",
    benchmark_run_id: null,
  };
}

export function createBatchManifest(batchId = DEFAULT_BATCH_ID, timestamp = nowIso(), options = {}) {
  const isDepthLadder = batchId === DEPTH_LADDER_BATCH_ID;
  const projectOrder = options.projects ?? (isDepthLadder ? DEPTH_LADDER_PROJECTS : MULTI_FAMILY_PROJECTS);
  const levelOrder = options.levels ?? (isDepthLadder ? DEPTH_LADDER_LEVELS : MULTI_FAMILY_LEVELS);
  const originals = projectOrder.map((project) => originalEntry(project, timestamp));
  const variants = projectOrder.flatMap((project) =>
    levelOrder.map((level) => variantEntry(project, level, timestamp)),
  );
  return {
    schema_version: BATCH_SCHEMA_VERSION,
    batch_id: safeBatchId(batchId),
    status: "pending",
    concurrency: 1,
    project_order: projectOrder,
    level_order: levelOrder,
    family_selection: isDepthLadder
      ? {
          status: "evidence_selected",
          rationale:
            "Chart, Math, Codec, and Closure have the strongest validated depth evidence; Cli, Collections, and Csv add deterministic lower-depth coverage. Chart-2 had no canonical variant/localization evidence at selection time.",
          excluded_chart_2_reason: "No canonical validated variants or completed localization artifacts were available.",
        }
      : null,
    frozen_benchmark_protocol: {
      agent: "mini-swe-agent",
      provider: "openai",
      model: "gpt-5.6",
      max_tool_calls: 50,
      max_test_runs: 5,
      startup_timeout_seconds: 30,
      execution_timeout_seconds: 300,
      repeats: 1,
    },
    research_framing: {
      public_status: "private",
      released_before_evaluation: false,
      source_bug_publicly_known: true,
      same_model_family: true,
      coupling_note:
        "Generation and evaluation may use Codex/GPT-family systems; results may be affected by generator-evaluator coupling.",
    },
    originals,
    variants,
    current_project: null,
    current_level: null,
    current_stage: null,
    resume_from: "verify_original",
    created_at: timestamp,
    updated_at: timestamp,
  };
}

async function atomicWriteJson(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const temporaryPath = `${filePath}.tmp-${process.pid}`;
  await fs.writeFile(temporaryPath, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
  await fs.rename(temporaryPath, filePath);
}

export async function ensureBatch(benchmarkRoot, batchId = DEFAULT_BATCH_ID) {
  const dir = batchDirectory(benchmarkRoot, batchId);
  const manifestPath = path.join(dir, "batch_manifest.json");
  if (!(await exists(manifestPath))) {
    await fs.mkdir(path.join(dir, "originals"), { recursive: true });
    await fs.mkdir(path.join(dir, "variants"), { recursive: true });
    await fs.mkdir(path.join(dir, "file_overlap_matrices"), { recursive: true });
    await atomicWriteJson(manifestPath, createBatchManifest(batchId));
  }
  return readBatch(benchmarkRoot, batchId);
}

export async function readBatch(benchmarkRoot, batchId = DEFAULT_BATCH_ID) {
  const dir = batchDirectory(benchmarkRoot, batchId);
  const manifest = JSON.parse(await fs.readFile(path.join(dir, "batch_manifest.json"), "utf8"));
  return { dir, manifest };
}

function allEntries(manifest) {
  return [...(manifest.originals ?? []), ...(manifest.variants ?? [])];
}

function findEntry(manifest, key) {
  return allEntries(manifest).find((entry) => entry.key === key);
}

export function isTerminalBatchEntry(entry) {
  if (entry.task_kind === "original") {
    if (["environment_blocked", "verification_failed"].includes(entry.status)) return true;
    return entry.status === "verified" && terminalBenchmarkStatuses.has(entry.benchmark_status);
  }
  if (!terminalVariantStatuses.has(entry.status)) return false;
  if (entry.status !== "validated") return true;
  return terminalBenchmarkStatuses.has(entry.benchmark_status);
}

export function nextBatchEntry(manifest) {
  for (const project of manifest.project_order ?? MULTI_FAMILY_PROJECTS) {
    const original = findEntry(manifest, `${project}-1:Original`);
    if (original && !isTerminalBatchEntry(original)) return original;
    for (const level of manifest.level_order ?? MULTI_FAMILY_LEVELS) {
      const variant = findEntry(manifest, `${project}-1:${level}`);
      if (variant && !isTerminalBatchEntry(variant)) return variant;
    }
  }
  return null;
}

function mergeEntry(entry, patch, timestamp) {
  const startedAt = entry.started_at ?? (patch.status === "running" ? timestamp : null);
  return {
    ...entry,
    ...patch,
    artifact_paths: Array.from(new Set([...(entry.artifact_paths ?? []), ...(patch.artifact_paths ?? [])])),
    started_at: startedAt,
    updated_at: timestamp,
  };
}

function batchStatus(manifest) {
  const entries = allEntries(manifest);
  if (entries.every(isTerminalBatchEntry)) return "completed";
  if (entries.some((entry) => entry.status === "running" || entry.benchmark_status === "running")) return "running";
  return "pending";
}

export async function checkpointBatchEntry(benchmarkRoot, batchId, key, patch) {
  const { dir, manifest } = await ensureBatch(benchmarkRoot, batchId);
  const current = findEntry(manifest, key);
  if (!current) throw new Error(`Batch entry not found: ${key}`);
  const timestamp = nowIso();
  const replacement = mergeEntry(current, patch, timestamp);
  const next = {
    ...manifest,
    originals: (manifest.originals ?? []).map((entry) => (entry.key === key ? replacement : entry)),
    variants: (manifest.variants ?? []).map((entry) => (entry.key === key ? replacement : entry)),
    updated_at: timestamp,
  };
  next.status = batchStatus(next);
  const active = allEntries(next).find((entry) => entry.status === "running" || entry.benchmark_status === "running");
  const resumeEntry = active ?? nextBatchEntry(next);
  next.current_project = resumeEntry?.project ?? null;
  next.current_level = resumeEntry?.level ?? null;
  next.current_stage = resumeEntry?.current_stage ?? null;
  next.resume_from = resumeEntry?.resume_from ?? null;
  await atomicWriteJson(path.join(dir, "batch_manifest.json"), next);
  return { dir, manifest: next, entry: replacement };
}

function metric(entry, name) {
  const value = entry.metrics?.[name];
  return value == null ? null : value;
}

export function variantMatrixRows(manifest) {
  return (manifest.variants ?? []).map((entry) => ({
    Project: entry.project,
    Bug: entry.bug,
    Level: entry.level,
    "Actual Semantic Steps": entry.semantic_inference_steps ?? null,
    "Variant ID": entry.variant_id ?? null,
    "Root Cause": entry.root_cause ?? null,
    "Gold Method": entry.gold_method ?? null,
    "Generation Status": entry.generation_status ?? entry.status,
    "Validation Status": entry.validation_status ?? (entry.status === "validated" ? "validated" : null),
    "Reproducibility Status": entry.reproducibility_status ?? (entry.status === "validated" ? "passed" : null),
    Consistency: entry.consistency ?? (entry.status === "validated" ? true : null),
    "Benchmark Eligible": entry.benchmark_eligible ?? (entry.status === "validated" ? true : false),
    "Benchmark Status": entry.benchmark_status ?? "not_run",
    "Gold Rank": metric(entry, "gold_rank"),
    "Hit@1": metric(entry, "hit_at_1"),
    "Hit@5": metric(entry, "hit_at_5"),
    "Hit@10": metric(entry, "hit_at_10"),
    MRR: metric(entry, "mrr"),
    "Tool Calls": metric(entry, "tool_calls"),
    Searches: metric(entry, "searches"),
    "Unique Files": metric(entry, "unique_files_read"),
    "Production Files": metric(entry, "production_files_read"),
    "Test Files": metric(entry, "test_files_read"),
    Tests: metric(entry, "test_runs"),
    Duration: metric(entry, "duration_ms"),
    "Gold File Read": metric(entry, "gold_file_read"),
    "First Gold File Position": metric(entry, "first_gold_file_read_position"),
    "Reasoning Workflow": entry.reasoning_workflow_path ?? null,
    "Top-10 Ranking": entry.ranking ?? [],
    "Failure/Skip Reason": entry.failure_reason ?? null,
  }));
}

export function benchmarkResultRows(manifest) {
  return allEntries(manifest).map((entry) => ({
    Project: entry.project,
    Bug: entry.bug,
    Level: entry.level,
    Task: entry.task_id ?? entry.variant_id ?? `${entry.project}-${entry.bug}`,
    Status: entry.benchmark_status ?? "not_run",
    "Actual Semantic Steps": entry.semantic_inference_steps ?? null,
    "Gold Rank": metric(entry, "gold_rank"),
    "Hit@1": metric(entry, "hit_at_1"),
    "Hit@5": metric(entry, "hit_at_5"),
    "Hit@10": metric(entry, "hit_at_10"),
    MRR: metric(entry, "mrr"),
    "Tool Calls": metric(entry, "tool_calls"),
    Searches: metric(entry, "searches"),
    "Unique Files": metric(entry, "unique_files_read"),
    "Production Files": metric(entry, "production_files_read"),
    "Test Files": metric(entry, "test_files_read"),
    Tests: metric(entry, "test_runs"),
    Duration: metric(entry, "duration_ms"),
    "Gold File Read": metric(entry, "gold_file_read"),
    "First Gold File Position": metric(entry, "first_gold_file_read_position"),
    "Reasoning Workflow": entry.reasoning_workflow_path ?? null,
    "Top-10 Ranking": entry.ranking ?? [],
    "Failure/Skip Reason": entry.failure_reason ?? null,
  }));
}

function csvCell(value) {
  if (value == null) return "";
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function rowsToCsv(rows) {
  if (!rows.length) return "";
  const columns = Object.keys(rows[0]);
  return `${columns.map(csvCell).join(",")}\n${rows
    .map((row) => columns.map((column) => csvCell(row[column])).join(","))
    .join("\n")}\n`;
}

function validCompletedEntries(entries) {
  return entries.filter(
    (entry) =>
      entry.benchmark_status === "completed" &&
      Number.isInteger(entry.metrics?.gold_rank) &&
      (entry.task_kind === "original" || entry.benchmark_eligible === true),
  );
}

function mean(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function median(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function accuracyCell(entries) {
  const valid = validCompletedEntries(entries);
  if (!valid.length) return { accuracy: null, numerator: 0, denominator: 0, display: "N/A" };
  const numerator = valid.filter((entry) => entry.metrics.gold_rank === 1).length;
  const accuracy = numerator / valid.length;
  return { accuracy, numerator, denominator: valid.length, display: `${accuracy.toFixed(2)} (${numerator}/${valid.length})` };
}

export function accuracyAtOneMatrix(manifest) {
  const levels = manifest.level_order ?? MULTI_FAMILY_LEVELS;
  const rows = (manifest.project_order ?? MULTI_FAMILY_PROJECTS).map((project) => ({
    project,
    bug: 1,
    cells: Object.fromEntries(
      levels.map((level) => [
        level,
        {
          ...accuracyCell((manifest.variants ?? []).filter((entry) => entry.project === project && entry.level === level)),
          task_key: `${project}-1:${level}`,
          variant_id: findEntry(manifest, `${project}-1:${level}`)?.variant_id ?? null,
        },
      ]),
    ),
  }));
  return { schema_version: "d4j-accuracy-at-one-matrix/v1", model: "gpt-5.6", agent: "mini-swe-agent", levels, rows, generated_at: nowIso() };
}

function accuracyAtOneCsvRows(matrix) {
  return matrix.rows.map((row) => ({
    Project: `${row.project}-${row.bug}`,
    ...Object.fromEntries(matrix.levels.map((level) => [level, row.cells[level]?.display ?? "N/A"])),
  }));
}

export function aggregateOriginalVsVariant(manifest, overlapMatrices = []) {
  const families = (manifest.project_order ?? MULTI_FAMILY_PROJECTS).map((project) => {
    const original = findEntry(manifest, `${project}-1:Original`);
    const variants = (manifest.level_order ?? MULTI_FAMILY_LEVELS).map((level) => findEntry(manifest, `${project}-1:${level}`));
    const overlaps = overlapMatrices.find((matrix) => matrix.project === project)?.pairs ?? [];
    return {
      project,
      original: original
        ? { status: original.benchmark_status, metrics: original.metrics ?? null, run_id: original.benchmark_run_id }
        : null,
      private_variants: variants.map((entry) => ({
        level: entry?.level,
        generation_status: entry?.status,
        benchmark_status: entry?.benchmark_status,
        metrics: entry?.metrics ?? null,
        run_id: entry?.benchmark_run_id ?? null,
        file_overlap: overlaps.find((pair) => pair.to === entry?.level) ?? null,
      })),
    };
  });
  return {
    schema_version: "d4j-original-vs-private-variants/v1",
    interpretation_guard:
      "Differences are descriptive and must not be treated as definitive proof of memorization or contamination.",
    families,
    generated_at: nowIso(),
  };
}

export function aggregateDepth(manifest) {
  const levels = manifest.level_order ?? MULTI_FAMILY_LEVELS;
  const originalValid = validCompletedEntries(manifest.originals ?? []);
  const originalAcc1 = accuracyCell(originalValid).accuracy;
  return {
    schema_version: "d4j-reasoning-depth-summary/v1",
    definition: "number of necessary semantic inference steps in the shortest valid failure-to-cause-and-method path",
    rows: (manifest.variants ?? []).map((entry) => ({
      project: entry.project,
      level: entry.level,
      actual_semantic_steps: entry.semantic_inference_steps ?? null,
      shortest_reasoning_path: entry.shortest_reasoning_path ?? [],
      shortcut_risks: entry.shortcut_risks ?? [],
      reasoning_level_status: entry.reasoning_level_status ?? "not_assessed",
    })),
    aggregates: levels.map((level) => {
      const variants = (manifest.variants ?? []).filter((entry) => entry.level === level);
      const valid = validCompletedEntries(variants);
      const numeric = (name) => valid.map((entry) => entry.metrics?.[name]).filter(Number.isFinite);
      const acc1 = accuracyCell(valid).accuracy;
      return {
        level,
        validated_variants: variants.filter((entry) => entry.status === "validated").length,
        valid_localization_runs: valid.length,
        accuracy_at_1: acc1,
        hit_at_5: mean(valid.map((entry) => Number(entry.metrics.hit_at_5))),
        hit_at_10: mean(valid.map((entry) => Number(entry.metrics.hit_at_10))),
        mean_gold_rank: mean(numeric("gold_rank")),
        median_gold_rank: median(numeric("gold_rank")),
        mean_tool_calls: mean(numeric("tool_calls")),
        mean_searches: mean(numeric("searches")),
        mean_unique_files: mean(numeric("unique_files_read")),
        mean_duration_ms: mean(numeric("duration_ms")),
        mean_first_gold_file_position: mean(numeric("first_gold_file_read_position")),
        accuracy_at_1_degradation_from_original: originalAcc1 == null || acc1 == null ? null : originalAcc1 - acc1,
      };
    }),
    original_reference: { valid_localization_runs: originalValid.length, accuracy_at_1: originalAcc1 },
    generated_at: nowIso(),
  };
}

function shortcutAuditRows(manifest) {
  const originalByProject = new Map((manifest.originals ?? []).map((entry) => [entry.project, entry]));
  const methods = (value) => new Set(String(value ?? "").split(";").map((item) => item.trim()).filter(Boolean));
  return allEntries(manifest).map((entry) => {
    const original = originalByProject.get(entry.project);
    const originalMethods = methods(original?.gold_method);
    const variantMethods = methods(entry.gold_method);
    const preservesOriginalMethod = entry.task_kind === "original"
      ? null
      : [...variantMethods].some((method) => originalMethods.has(method));
    const addsSemanticDependencies = entry.task_kind === "original" || entry.semantic_inference_steps == null || original?.semantic_inference_steps == null
      ? null
      : entry.semantic_inference_steps > original.semantic_inference_steps;
    return {
      Project: entry.project,
      Level: entry.level,
      Task: entry.task_id ?? entry.variant_id ?? `${entry.project}-${entry.bug}`,
      "Benchmark Status": entry.benchmark_status ?? "not_run",
      "Benchmark Eligible": entry.task_kind === "original" ? true : entry.benchmark_eligible ?? false,
      "Fault In New Method Location": entry.task_kind === "original" || variantMethods.size === 0 ? null : !preservesOriginalMethod,
      "Preserves Original Fault Method": preservesOriginalMethod,
      "Introduces Additional Semantic Dependencies": addsSemanticDependencies,
      "Additional Semantic Step Count": addsSemanticDependencies == null ? null : entry.semantic_inference_steps - original.semantic_inference_steps,
      "Gold Method In Test Source": entry.shortcut_audit?.gold_method_in_test_source ?? null,
      "Gold Class In Test Source": entry.shortcut_audit?.gold_class_in_test_source ?? null,
      "Gold Method In Test Name": entry.shortcut_audit?.gold_method_in_test_name ?? null,
      "Gold Class In Stack Trace": entry.shortcut_audit?.gold_class_in_stack_trace ?? null,
      "Gold Method In Stack Trace": entry.shortcut_audit?.gold_method_in_stack_trace ?? null,
      "Failure Names Gold Method": entry.shortcut_audit?.failure_message_names_gold_method ?? null,
      "Trigger Directly Calls Gold": entry.shortcut_audit?.trigger_directly_calls_gold_method ?? null,
      "Gold File Obvious From Stack": entry.shortcut_audit?.gold_file_obvious_from_stack_trace ?? null,
      "Searched Exact Test Name": entry.shortcut_audit?.searched_exact_test_name ?? null,
      "Searched Exact Exception": entry.shortcut_audit?.searched_exact_exception_message ?? null,
      "Searched Gold Method": entry.shortcut_audit?.searched_gold_method_name ?? null,
      "First Gold File Position": metric(entry, "first_gold_file_read_position"),
      "First Gold Method Identified": entry.shortcut_audit?.first_gold_method_identified_position ?? null,
    };
  });
}

function overlapForFiles(from, to, fromFiles, toFiles) {
  const left = new Set(fromFiles);
  const right = new Set(toFiles);
  const shared = [...left].filter((file) => right.has(file)).sort();
  const originalOnly = [...left].filter((file) => !right.has(file)).sort();
  const variantOnly = [...right].filter((file) => !left.has(file)).sort();
  const unionCount = new Set([...left, ...right]).size;
  return {
    from,
    to,
    jaccard: unionCount ? shared.length / unionCount : null,
    shared_files: shared,
    original_only_files: originalOnly,
    variant_only_files: variantOnly,
    intersection_count: shared.length,
    union_count: unionCount,
  };
}

async function benchmarkFilesForEntry(benchmarkRoot, entry) {
  if (entry?.benchmark_status !== "completed") return [];
  const repoRoot = path.dirname(benchmarkRoot);
  const runArtifact = [...(entry.artifact_paths ?? [])]
    .reverse()
    .find((artifactPath) => /^benchmark_runs\//.test(artifactPath) && /\/run-\d+\/?$/.test(artifactPath));
  if (!runArtifact) return [];
  const runDir = safeResolve(repoRoot, runArtifact);
  const manifest = JSON.parse(await fs.readFile(path.join(runDir, "run_manifest.json"), "utf8"));
  return (manifest.metrics?.files ?? []).map((file) => file.file).filter(Boolean).sort();
}

async function writeFileOverlapMatrices(benchmarkRoot, dir, manifest) {
  const outputDir = path.join(dir, "file_overlap_matrices");
  await fs.mkdir(outputDir, { recursive: true });
  const matrices = [];
  for (const project of manifest.project_order ?? MULTI_FAMILY_PROJECTS) {
    const original = findEntry(manifest, `${project}-1:Original`);
    const originalFiles = await benchmarkFilesForEntry(benchmarkRoot, original);
    const pairs = [];
    for (const level of manifest.level_order ?? MULTI_FAMILY_LEVELS) {
      const variant = findEntry(manifest, `${project}-1:${level}`);
      const variantFiles = await benchmarkFilesForEntry(benchmarkRoot, variant);
      pairs.push(overlapForFiles("Original", level, originalFiles, variantFiles));
    }
    const matrix = {
      schema_version: "d4j-batch-file-overlap/v1",
      project,
      bug: 1,
      pairs,
      generated_at: nowIso(),
    };
    await atomicWriteJson(path.join(outputDir, `${project}-1.json`), matrix);
    matrices.push(matrix);
  }
  return matrices;
}

function markdownCell(value) {
  if (value == null || value === "") return "null";
  return String(value).replaceAll("|", "\\|").replaceAll("\n", " ");
}

function metricMatrixRows(manifest, metricName) {
  const levels = manifest.level_order ?? MULTI_FAMILY_LEVELS;
  return (manifest.project_order ?? MULTI_FAMILY_PROJECTS).map((project) => {
    const cells = levels.map((level) => {
      const entries = validCompletedEntries((manifest.variants ?? []).filter((entry) => entry.project === project && entry.level === level));
      if (!entries.length) return "N/A";
      const numerator = entries.filter((entry) => Boolean(entry.metrics?.[metricName])).length;
      return `${(numerator / entries.length).toFixed(2)} (${numerator}/${entries.length})`;
    });
    return `| ${project}-1 | ${cells.join(" | ")} |`;
  }).join("\n");
}

function batchReport(manifest, matrix, overlapMatrices, acc1, depth) {
  const entries = allEntries(manifest);
  const completed = entries.filter(isTerminalBatchEntry).length;
  const variantRows = matrix
    .map((row) =>
      `| ${markdownCell(row.Project)} | ${markdownCell(row.Level)} | ${markdownCell(row["Variant ID"])} | ${markdownCell(row["Generation Status"])} | ${markdownCell(row["Validation Status"])} | ${markdownCell(row["Reproducibility Status"])} | ${markdownCell(row["Benchmark Status"])} | ${markdownCell(row["Gold Rank"])} | ${markdownCell(row["Hit@5"])} | ${markdownCell(row["Hit@10"])} | ${markdownCell(row["Failure/Skip Reason"])} |`,
    )
    .join("\n");
  const overlapRows = overlapMatrices
    .flatMap((matrixItem) => matrixItem.pairs.map((pair) => `| ${matrixItem.project} | ${pair.to} | ${markdownCell(pair.jaccard)} | ${pair.shared_files.length} | ${pair.original_only_files.length} | ${pair.variant_only_files.length} |`))
    .join("\n");
  const levelHeaders = (manifest.level_order ?? MULTI_FAMILY_LEVELS).join(" | ");
  const levelRules = (manifest.level_order ?? MULTI_FAMILY_LEVELS).map(() => "---:").join(" | ");
  const acc1Rows = acc1.rows.map((row) => `| ${row.project}-${row.bug} | ${acc1.levels.map((level) => row.cells[level].display).join(" | ")} |`).join("\n");
  const depthRows = depth.aggregates.map((row) => `| ${row.level} | ${row.validated_variants} | ${row.valid_localization_runs} | ${markdownCell(row.accuracy_at_1)} | ${markdownCell(row.hit_at_5)} | ${markdownCell(row.hit_at_10)} | ${markdownCell(row.mean_gold_rank)} | ${markdownCell(row.median_gold_rank)} | ${markdownCell(row.mean_tool_calls)} | ${markdownCell(row.mean_searches)} | ${markdownCell(row.mean_unique_files)} | ${markdownCell(row.mean_duration_ms)} | ${markdownCell(row.mean_first_gold_file_position)} |`).join("\n");
  const failures = entries.filter((entry) => entry.failure_reason).map((entry) => `- ${entry.key}: ${entry.status}/${entry.benchmark_status} - ${entry.failure_reason}`).join("\n") || "- None recorded.";
  return `# Controlled Reasoning Fault Localization Batch

- Batch: ${manifest.batch_id}
- Status: ${manifest.status}
- Terminal entries: ${completed}/${entries.length}
- Concurrency: ${manifest.concurrency}
- Updated: ${manifest.updated_at}
- Model: ${manifest.frozen_benchmark_protocol.model}
- Execution timeout: ${manifest.frozen_benchmark_protocol.execution_timeout_seconds} seconds

Missing values are represented as \`null\`; failed, skipped, and unrun tasks are never represented as zero.

## 1. Experiment Configuration

The frozen localization protocol uses mini-swe-agent, GPT-5.6, 50 tool calls, 5 failing-test runs, a 30-second startup timeout, a 300-second execution timeout, one repeat, and structured Top-10 submission. Accuracy@1 is primary; Hit@5, Hit@10, gold rank, and MRR are secondary.

## 2. Selected Bug Families

${(manifest.project_order ?? []).map((project) => `- ${project}-1`).join("\n")}

${manifest.family_selection?.rationale ?? "This batch predates the seven-family evidence selection."}

## 3. Variant Generation Status

| Project | Level | Variant ID | Generation | Validation | Reproducibility | Localization | Gold Rank | Hit@5 | Hit@10 | Failure/Skip Reason |
| --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |
${variantRows}

## 4. Validation Status

Only variants with fresh baseline-pass, variant-fail, and deterministic three-run evidence are marked benchmark eligible. See \`variant_matrix.csv\` and each canonical \`validation.json\`.

## 5. Localization Results

See \`benchmark_results.csv\`. Non-completed runs have null ranking metrics and are excluded from aggregation.

## 6. Accuracy@1 Matrix

| Task | ${levelHeaders} |
| --- | ${levelRules} |
${acc1Rows}

## 7. Hit@5 Matrix

| Task | ${levelHeaders} |
| --- | ${levelRules} |
${metricMatrixRows(manifest, "hit_at_5")}

## 8. Hit@10 Matrix

| Task | ${levelHeaders} |
| --- | ${levelRules} |
${metricMatrixRows(manifest, "hit_at_10")}

## 9. Depth Statistics

| Level | Validated | Valid Runs | Acc@1 | Hit@5 | Hit@10 | Mean Rank | Median Rank | Mean Tools | Mean Searches | Mean Files | Mean Duration ms | Mean First Gold Position |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
${depthRows}

These descriptive pilot aggregates do not establish statistical significance.

## 10. Shortcut Audit

Literal test, stack-trace, and observable search exposure fields are in \`shortcut_audit.csv\`. They are covariates, not binary evidence of memorization.

## 11. Failures

${failures}

## 12. Depth-Unachievable Cases

\`depth_unachievable\` and dependency skips are retained as scientific outcomes; no level is forced to fill the table.

## 13. Threats to Validity

- Sample sizes are small and usually n=1 per task.
- Source bugs are public even though exact semantic variants are private.
- Generator and evaluator use the same model family, creating possible coupling.
- Test and stack-trace disclosures may create family-specific localization shortcuts.

## 14. Reproducibility Information

- Batch artifacts: \`benchmark_runs/batches/${manifest.batch_id}/\`
- Resume: \`D4J_API_PORT=8790 pnpm run batch:resume -- --batch=${manifest.batch_id}\`
- Durable events: \`batch_events.jsonl\`
- Observable workflows: \`reasoning_workflow_summary.json\`

## File Overlap Evidence

| Project | Variant | Jaccard | Shared | Original Only | Variant Only |
| --- | --- | ---: | ---: | ---: | ---: |
${overlapRows}

The comparison is descriptive and is not definitive evidence of memorization or contamination.
`;
}

export async function writeBatchOutputs(benchmarkRoot, batchId = DEFAULT_BATCH_ID) {
  const { dir, manifest } = await readBatch(benchmarkRoot, batchId);
  const matrix = variantMatrixRows(manifest);
  const benchmarkRows = benchmarkResultRows(manifest);
  const depth = aggregateDepth(manifest);
  const acc1 = accuracyAtOneMatrix(manifest);
  const fileOverlapMatrices = await writeFileOverlapMatrices(benchmarkRoot, dir, manifest);
  const comparison = aggregateOriginalVsVariant(manifest, fileOverlapMatrices);
  const workflow = {
    schema_version: "d4j-workflow-summary/v1",
    runs_with_workflow: allEntries(manifest).filter((entry) => entry.reasoning_workflow_path).length,
    entries: allEntries(manifest).map((entry) => ({
      key: entry.key,
      benchmark_status: entry.benchmark_status,
      reasoning_workflow_path: entry.reasoning_workflow_path ?? null,
    })),
    generated_at: nowIso(),
  };
  await fs.writeFile(path.join(dir, "variant_matrix.csv"), rowsToCsv(matrix));
  await fs.writeFile(path.join(dir, "benchmark_results.csv"), rowsToCsv(benchmarkRows));
  await fs.writeFile(path.join(dir, "acc1_matrix.csv"), rowsToCsv(accuracyAtOneCsvRows(acc1)));
  await fs.writeFile(path.join(dir, "shortcut_audit.csv"), rowsToCsv(shortcutAuditRows(manifest)));
  await atomicWriteJson(path.join(dir, "acc1_matrix.json"), acc1);
  await atomicWriteJson(path.join(dir, "original_vs_variant_summary.json"), comparison);
  await atomicWriteJson(path.join(dir, "depth_summary.json"), depth);
  await atomicWriteJson(path.join(dir, "workflow_summary.json"), workflow);
  await atomicWriteJson(path.join(dir, "reasoning_workflow_summary.json"), workflow);
  await fs.writeFile(path.join(dir, "REPORT.md"), batchReport(manifest, matrix, fileOverlapMatrices, acc1, depth));
  return { dir, manifest, matrix, benchmarkRows, comparison, depth, acc1, workflow, fileOverlapMatrices };
}
