import fs from "node:fs/promises";
import path from "node:path";
import { discoverBenchmarkRunRecords, parseBenchmarkDurationMs } from "./benchmarkStore.mjs";
import { exists } from "./variantLibrary.mjs";

export const ACCURACY_SCHEMA_VERSION = "d4j-accuracy-analysis/v1";
export const CANONICAL_RESULT_SCHEMA_VERSION = "d4j-canonical-localization-result/v1";
export const DEFAULT_TARGET_RUNS = 5;
export const ACCURACY_DEPTHS = ["L10", "L30", "L50", "L70", "L90"];
export const ACCURACY_FAMILIES = [
  { project: "Chart", bug_id: 1 },
  { project: "Chart", bug_id: 2 },
  { project: "Math", bug_id: 1 },
  { project: "Cli", bug_id: 1 },
  { project: "Collections", bug_id: 1 },
  { project: "Codec", bug_id: 1 },
  { project: "Gson", bug_id: 1 },
  { project: "Time", bug_id: 1 },
  { project: "Closure", bug_id: 1 },
];
export const SEVEN_FAMILY_PILOT_FAMILIES = [
  { project: "Chart", bug_id: 1 },
  { project: "Math", bug_id: 1 },
  { project: "Cli", bug_id: 1 },
  { project: "Collections", bug_id: 1 },
  { project: "Codec", bug_id: 1 },
  { project: "Closure", bug_id: 1 },
  { project: "Csv", bug_id: 1 },
];
export const FROZEN_PROMPT_VERSION = "d4j-localization-only/v2";
export const FROZEN_PROMPT_HASH = "845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89";
export const accuracyMetricNames = new Set(["at1", "at5", "at10", "mrr", "mean_rank"]);
const batchPrecedence = ["multi-family-l10-l30-l50-v1", "seven-family-l10-l90-v1"];

function familyId(project, bugId) {
  return `${project}-${bugId}`;
}

function cellKey(project, bugId, depth) {
  return `${familyId(project, bugId)}:${depth}`;
}

function normalizeRunStatus(status) {
  if (status === "provider_not_configured") return "provider_error";
  if (["agent_protocol_error", "protocol_violation"].includes(status)) return "protocol_error";
  return status === "completed" || status === "timeout" || status === "invalid_ranking" || status === "failed"
    ? status
    : String(status ?? "failed");
}

function availabilityForEntry(entry) {
  if (!entry) return "not_attempted";
  if (entry.status === "validated" && entry.benchmark_eligible !== false) return "available";
  if (entry.status === "generation_failed" || entry.status === "candidate_rejected") return "generation_failed";
  if (["validation_failed", "reproducibility_failed", "benchmark_ineligible"].includes(entry.status)) {
    return entry.reasoning_level_status === "depth_rejected" ? "depth_unachievable" : "validation_failed";
  }
  if (entry.status === "depth_unachievable") return "depth_unachievable";
  if (entry.status === "not_attempted_due_to_dependency") return "dependency_skipped";
  return "not_attempted";
}

function excludedVariantCount(entry) {
  return entry && ["generation_failed", "candidate_rejected", "validation_failed", "reproducibility_failed", "benchmark_ineligible"].includes(entry.status)
    ? 1
    : 0;
}

async function readBatchManifests(benchmarkRoot) {
  const manifests = [];
  for (const batchId of batchPrecedence) {
    const filePath = path.join(benchmarkRoot, "batches", batchId, "batch_manifest.json");
    if (await exists(filePath)) manifests.push(JSON.parse(await fs.readFile(filePath, "utf8")));
  }
  return manifests;
}

export function buildAccuracyTaskRegistry(batchManifests = [], families = ACCURACY_FAMILIES) {
  const cells = new Map();
  const originals = new Map();
  for (const family of families) {
    const familyName = familyId(family.project, family.bug_id);
    originals.set(familyName, {
      family: familyName,
      project: family.project,
      bug_id: family.bug_id,
      depth: "Original",
      task_id: familyName,
      task_type: "original",
      availability: "not_attempted",
      exclusion_reasons: ["No verified canonical original run is registered."],
      valid_variant_count: 0,
      excluded_variant_count: 0,
    });
    for (const depth of ACCURACY_DEPTHS) {
      cells.set(cellKey(family.project, family.bug_id, depth), {
        family: familyName,
        project: family.project,
        bug_id: family.bug_id,
        depth,
        task_id: null,
        variant_id: null,
        task_type: "variant",
        availability: "not_attempted",
        exclusion_reasons: ["No canonical variant attempt is registered for this depth."],
        valid_variant_count: 0,
        excluded_variant_count: 0,
      });
    }
  }

  for (const manifest of batchManifests) {
    for (const entry of manifest.originals ?? []) {
      const key = familyId(entry.project, entry.bug);
      if (!originals.has(key)) continue;
      const available = entry.status === "verified";
      originals.set(key, {
        ...originals.get(key),
        task_id: entry.task_id ?? key,
        gold_method: entry.gold_method ?? null,
        availability: available ? "available" : "not_attempted",
        exclusion_reasons: available ? [] : [entry.failure_reason ?? "Original verification did not complete."],
        batch_id: manifest.batch_id,
      });
    }
    for (const entry of manifest.variants ?? []) {
      const key = cellKey(entry.project, entry.bug, entry.level);
      if (!cells.has(key)) continue;
      const availability = availabilityForEntry(entry);
      cells.set(key, {
        ...cells.get(key),
        task_id: entry.variant_id ?? null,
        variant_id: entry.variant_id ?? null,
        gold_method: entry.gold_method ?? null,
        availability,
        exclusion_reasons: availability === "available" ? [] : [entry.failure_reason ?? `Task availability is ${availability}.`],
        valid_variant_count: availability === "available" ? 1 : 0,
        excluded_variant_count: excludedVariantCount(entry),
        generation_status: entry.status,
        validation_status: entry.validation_status ?? null,
        benchmark_eligible: entry.benchmark_eligible ?? false,
        actual_semantic_steps: entry.semantic_inference_steps ?? null,
        batch_id: manifest.batch_id,
      });
    }
  }

  const byTask = new Map();
  for (const task of cells.values()) {
    const original = originals.get(task.family);
    const originalMethods = new Set(String(original?.gold_method ?? "").split(";").map((item) => item.trim()).filter(Boolean));
    const variantMethods = new Set(String(task.gold_method ?? "").split(";").map((item) => item.trim()).filter(Boolean));
    const preserves = [...variantMethods].some((method) => originalMethods.has(method));
    task.fault_method_relocated = variantMethods.size ? !preserves : null;
    task.original_faulty_method_preserved = variantMethods.size ? preserves : null;
  }
  for (const task of [...originals.values(), ...cells.values()]) {
    if (task.task_id) byTask.set(task.task_id, task);
  }
  return { cells, originals, byTask };
}

function canonicalRun(record, registry, families = ACCURACY_FAMILIES) {
  const manifest = record.manifest ?? {};
  const evaluation = record.evaluation ?? {};
  const ranking = record.ranking ?? {};
  const source = manifest.source ?? {};
  const project = String(source.project ?? "");
  const bugId = Number(source.bug_id);
  const family = familyId(project, bugId);
  const task = registry.byTask.get(manifest.task_id);
  const inferredDepth = manifest.task_type === "original"
    ? "Original"
    : String(source.variant_id ?? manifest.task_id).match(/-(L\d+)-/)?.[1] ?? "Unknown";
  const depth = task?.depth ?? inferredDepth;
  const protocolVersion = manifest.prompt?.version ?? null;
  const promptHash = manifest.prompt?.base_prompt_sha256 ?? null;
  const reasons = [];
  if (!families.some((item) => item.project === project && item.bug_id === bugId)) reasons.push("family_not_in_accuracy_cohort");
  if (!task) reasons.push("task_not_in_canonical_cell");
  if (task && task.availability !== "available") reasons.push(`task_availability_${task.availability}`);
  if (protocolVersion !== FROZEN_PROMPT_VERSION) reasons.push("protocol_version_not_frozen");
  if (promptHash !== FROZEN_PROMPT_HASH) reasons.push("prompt_hash_not_frozen");
  const status = normalizeRunStatus(manifest.status);
  const predictions = Array.isArray(ranking.predictions) ? ranking.predictions : [];
  const rankingValid = status === "completed" && ranking.parse_status === "parsed" && predictions.length === 10;
  const goldRank = rankingValid && Number.isInteger(evaluation.gold_rank) ? evaluation.gold_rank : null;
  const hitAt1 = rankingValid ? goldRank === 1 : null;
  const hitAt5 = rankingValid ? goldRank != null && goldRank <= 5 : null;
  const hitAt10 = rankingValid ? goldRank != null && goldRank <= 10 : null;
  return {
    schema_version: CANONICAL_RESULT_SCHEMA_VERSION,
    run_id: manifest.id ?? record.id,
    run_number: manifest.run_id ?? null,
    agent_id: manifest.agent?.agent_id ?? null,
    agent: manifest.agent?.framework ?? null,
    model: manifest.agent?.model ?? null,
    project,
    bug_id: String(bugId),
    family,
    task_id: manifest.task_id ?? null,
    task_type: manifest.task_type ?? null,
    variant_id: source.variant_id ?? null,
    depth,
    base_bug: family,
    gold_methods: evaluation.gold_methods ?? [],
    predictions,
    gold_rank: goldRank,
    hit_at_1: hitAt1,
    hit_at_5: hitAt5,
    hit_at_10: hitAt10,
    reciprocal_rank: rankingValid ? (goldRank == null ? 0 : 1 / goldRank) : null,
    status,
    original_status: manifest.status ?? null,
    eligibility: reasons.length ? "excluded" : "eligible",
    eligible: reasons.length === 0,
    eligibility_reasons: reasons,
    included_in_accuracy: reasons.length === 0 && rankingValid,
    ranking_valid: rankingValid,
    availability: task?.availability ?? "not_attempted",
    protocol_version: protocolVersion,
    prompt_hash: promptHash,
    started_at: manifest.started_at ?? null,
    completed_at: manifest.completed_at ?? null,
    duration_ms: parseBenchmarkDurationMs(record.commands) ?? manifest.metrics?.duration_ms ?? null,
    artifact_path: record.artifact_path,
    shortcut_audit: {
      ...(record.shortcut_audit ?? {}),
      fault_method_relocated: task?.fault_method_relocated ?? null,
      original_faulty_method_preserved: task?.original_faulty_method_preserved ?? null,
    },
  };
}

function mean(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function ratioMetric(completed, predicate) {
  if (!completed.length) return { value: null, numerator: 0, denominator: 0 };
  const numerator = completed.filter(predicate).length;
  return { value: numerator / completed.length, numerator, denominator: completed.length };
}

export function summarizeAccuracyRecords(records, { availability = "available", targetRuns = DEFAULT_TARGET_RUNS, validVariantCount = 1, excludedVariantCount = 0, exclusionReasons = [] } = {}) {
  const cohort = records.filter((record) => record.eligible);
  const completed = cohort.filter((record) => record.status === "completed" && record.ranking_valid !== false);
  const ranked = completed.map((record) => record.gold_rank).filter(Number.isInteger);
  const reciprocalRanks = completed.map((record) => record.gold_rank == null ? 0 : 1 / record.gold_rank);
  const unavailable = availability !== "available";
  const at1 = unavailable ? { value: null, numerator: 0, denominator: 0 } : ratioMetric(completed, (record) => record.gold_rank === 1);
  const at5 = unavailable ? { value: null, numerator: 0, denominator: 0 } : ratioMetric(completed, (record) => record.gold_rank != null && record.gold_rank <= 5);
  const at10 = unavailable ? { value: null, numerator: 0, denominator: 0 } : ratioMetric(completed, (record) => record.gold_rank != null && record.gold_rank <= 10);
  const metricDenominator = unavailable ? 0 : completed.length;
  const runExclusions = records
    .filter((record) => !record.included_in_accuracy)
    .flatMap((record) => record.eligible ? [`run_status_${record.status}`] : record.eligibility_reasons ?? []);
  const missingResultReasons = unavailable || completed.length
    ? []
    : [cohort.length ? "no_eligible_completed_runs" : "not_attempted"];
  return {
    availability,
    n_attempted: unavailable ? 0 : cohort.length,
    n_completed: unavailable ? 0 : cohort.filter((record) => record.status === "completed").length,
    n_eligible: metricDenominator,
    target_runs: availability === "available" ? targetRuns * Math.max(1, validVariantCount) : 0,
    accuracy_at_1: at1,
    accuracy_at_5: at5,
    accuracy_at_10: at10,
    mean_reciprocal_rank: { value: metricDenominator ? mean(reciprocalRanks) : null, denominator: metricDenominator },
    mean_gold_rank: { value: ranked.length ? mean(ranked) : null, denominator: metricDenominator, observed_ranks: ranked.length },
    valid_variant_count: validVariantCount,
    excluded_variant_count: excludedVariantCount,
    exclusion_reasons: [...new Set([...exclusionReasons.filter(Boolean), ...runExclusions, ...missingResultReasons])],
  };
}

function metricValue(cell, metric) {
  if (metric === "at1") return cell.accuracy_at_1;
  if (metric === "at5") return cell.accuracy_at_5;
  if (metric === "at10") return cell.accuracy_at_10;
  if (metric === "mrr") return cell.mean_reciprocal_rank;
  return cell.mean_gold_rank;
}

export function formatAccuracyCell(cell, metric = "at1") {
  const selected = metricValue(cell, metric);
  if (selected.value == null) return { value: null, numerator: 0, denominator: 0, display: "N/A" };
  const displayValue = metric === "mrr" ? selected.value.toFixed(3) : selected.value.toFixed(2);
  const sample = metric.startsWith("at") ? `${selected.numerator}/${selected.denominator}` : `n=${selected.denominator}`;
  return { ...selected, display: `${displayValue} (${sample})` };
}

function aggregateAcrossCells(cells) {
  const records = cells.flatMap((cell) => cell.records);
  const validVariantCount = cells.reduce((sum, cell) => sum + cell.valid_variant_count, 0);
  const excludedVariantCount = cells.reduce((sum, cell) => sum + cell.excluded_variant_count, 0);
  const summary = summarizeAccuracyRecords(records, {
    availability: cells.some((cell) => cell.availability === "available") ? "available" : "not_attempted",
    targetRuns: 1,
    validVariantCount: 1,
    excludedVariantCount,
    exclusionReasons: cells.flatMap((cell) => cell.exclusion_reasons),
  });
  return {
    ...summary,
    target_runs: cells.reduce((sum, cell) => sum + cell.target_runs, 0),
    valid_variant_count: validVariantCount,
    excluded_variant_count: excludedVariantCount,
  };
}

export function aggregateCanonicalResults(runRecords, registry, { targetRuns = DEFAULT_TARGET_RUNS, families = ACCURACY_FAMILIES } = {}) {
  const cells = [];
  for (const family of families) {
    for (const depth of ACCURACY_DEPTHS) {
      const task = registry.cells.get(cellKey(family.project, family.bug_id, depth));
      const matching = runRecords.filter((record) => record.family === task.family && record.depth === depth);
      const summary = summarizeAccuracyRecords(matching, {
        availability: task.availability,
        targetRuns,
        validVariantCount: task.valid_variant_count,
        excludedVariantCount: task.excluded_variant_count,
        exclusionReasons: task.exclusion_reasons,
      });
      cells.push({ ...task, ...summary, records: matching });
    }
  }

  const originals = families.map((family) => {
    const task = registry.originals.get(familyId(family.project, family.bug_id));
    const matching = runRecords.filter((record) => record.family === task.family && record.depth === "Original");
    return { ...task, ...summarizeAccuracyRecords(matching, { availability: task.availability, targetRuns, exclusionReasons: task.exclusion_reasons }), records: matching };
  });
  const originalByFamily = new Map(originals.map((item) => [item.family, item]));
  for (const cell of cells) {
    const original = originalByFamily.get(cell.family);
    cell.original_accuracy_at_1 = original?.accuracy_at_1.value ?? null;
    cell.variant_accuracy_at_1 = cell.accuracy_at_1.value;
    cell.delta_accuracy_at_1 = cell.original_accuracy_at_1 == null || cell.variant_accuracy_at_1 == null
      ? null
      : cell.variant_accuracy_at_1 - cell.original_accuracy_at_1;
  }
  const depthSummary = ACCURACY_DEPTHS.map((depth) => ({
    depth,
    ...aggregateAcrossCells(cells.filter((cell) => cell.depth === depth)),
  }));
  const familySummary = families.map((family) => ({
    family: familyId(family.project, family.bug_id),
    project: family.project,
    bug_id: family.bug_id,
    original: originalByFamily.get(familyId(family.project, family.bug_id)),
    depths: cells.filter((cell) => cell.family === familyId(family.project, family.bug_id)),
  }));
  return { cells, originals, depthSummary, familySummary };
}

function csvCell(value) {
  if (value == null) return "";
  const text = typeof value === "object" ? JSON.stringify(value) : String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function rowsToCsv(rows) {
  if (!rows.length) return "";
  const columns = Object.keys(rows[0]);
  return `${columns.join(",")}\n${rows.map((row) => columns.map((column) => csvCell(row[column])).join(",")).join("\n")}\n`;
}

function statisticalRow(cell) {
  return {
    model: "gpt-5.6",
    agent: "mini-swe-agent",
    family: cell.family,
    project: cell.project,
    bug_id: cell.bug_id,
    depth: cell.depth,
    availability: cell.availability,
    n_attempted: cell.n_attempted,
    n_completed: cell.n_completed,
    n_eligible: cell.n_eligible,
    target_runs: cell.target_runs,
    accuracy_at_1: cell.accuracy_at_1.value,
    accuracy_at_5: cell.accuracy_at_5.value,
    accuracy_at_10: cell.accuracy_at_10.value,
    mean_reciprocal_rank: cell.mean_reciprocal_rank.value,
    mean_gold_rank: cell.mean_gold_rank.value,
    valid_variant_count: cell.valid_variant_count,
    excluded_variant_count: cell.excluded_variant_count,
    exclusion_reasons: cell.exclusion_reasons,
  };
}

function accuracyReport(analysis) {
  const header = `| Family | ${ACCURACY_DEPTHS.join(" | ")} |`;
  const rule = `| --- | ${ACCURACY_DEPTHS.map(() => "---:").join(" | ")} |`;
  const matrix = analysis.matrix.rows.map((row) => `| ${row.family} | ${ACCURACY_DEPTHS.map((depth) => row.cells[depth].metrics.at1.display).join(" | ")} |`).join("\n");
  const depthRows = analysis.depth_summary.map((row) => `| ${row.depth} | ${row.n_eligible} | ${row.accuracy_at_1 ?? "null"} | ${row.accuracy_at_5 ?? "null"} | ${row.accuracy_at_10 ?? "null"} | ${row.mean_reciprocal_rank ?? "null"} | ${row.mean_gold_rank ?? "null"} |`).join("\n");
  return `# Accuracy-First CRFLB Analysis\n\n- Generated: ${analysis.generated_at}\n- Frozen prompt: ${analysis.experiment_config.protocol_version}\n- Target runs per task: ${analysis.experiment_config.target_runs}\n- Eligible completed runs: ${analysis.summary.eligible_completed_runs}\n- Excluded historical runs: ${analysis.summary.excluded_runs}\n\nUnavailable tasks remain null and are never converted to model failures.\n\n## Accuracy@1 Matrix\n\n${header}\n${rule}\n${matrix}\n\n## Depth-Level Summary\n\n| Depth | Eligible Runs | Acc@1 | Acc@5 | Acc@10 | MRR | Mean Gold Rank |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n${depthRows}\n\n## Interpretation\n\nThis is descriptive pilot evidence. Availability states describe task construction; accuracy uses only eligible completed localization runs. Missing repetitions, generation failures, validation failures, timeouts, protocol errors, and invalid rankings are excluded from metric denominators.\n`;
}

export function selectAccuracyMetric(analysis, metric = "at1") {
  const selectedMetric = accuracyMetricNames.has(metric) ? metric : "at1";
  return {
    ...analysis,
    selected_metric: selectedMetric,
    matrix: {
      ...analysis.matrix,
      metric: selectedMetric,
      rows: analysis.matrix.rows.map((row) => ({
        ...row,
        cells: Object.fromEntries(Object.entries(row.cells).map(([depth, cell]) => [depth, { ...cell, selected: cell.metrics[selectedMetric] }])),
      })),
    },
  };
}

export async function buildAccuracyAnalysis({ benchmarkRoot, repoRoot, targetRuns = DEFAULT_TARGET_RUNS }) {
  const [batchManifests, discovered] = await Promise.all([
    readBatchManifests(benchmarkRoot),
    discoverBenchmarkRunRecords(benchmarkRoot, repoRoot),
  ]);
  const registry = buildAccuracyTaskRegistry(batchManifests);
  const runLevelResults = discovered.map((record) => canonicalRun(record, registry));
  const aggregated = aggregateCanonicalResults(runLevelResults, registry, { targetRuns });
  const pilotManifests = batchManifests.filter((manifest) => manifest.batch_id === "seven-family-l10-l90-v1");
  const pilotRegistry = buildAccuracyTaskRegistry(pilotManifests, SEVEN_FAMILY_PILOT_FAMILIES);
  const pilotRunLevelResults = discovered.map((record) => canonicalRun(record, pilotRegistry, SEVEN_FAMILY_PILOT_FAMILIES));
  const pilotAggregated = aggregateCanonicalResults(pilotRunLevelResults, pilotRegistry, {
    targetRuns,
    families: SEVEN_FAMILY_PILOT_FAMILIES,
  });
  const rows = ACCURACY_FAMILIES.map((family) => {
    const familyName = familyId(family.project, family.bug_id);
    return {
      family: familyName,
      project: family.project,
      bug_id: family.bug_id,
      cells: Object.fromEntries(ACCURACY_DEPTHS.map((depth) => {
        const cell = aggregated.cells.find((item) => item.family === familyName && item.depth === depth);
        return [depth, {
          ...statisticalRow(cell),
          original_accuracy_at_1: cell.original_accuracy_at_1,
          variant_accuracy_at_1: cell.variant_accuracy_at_1,
          delta_accuracy_at_1: cell.delta_accuracy_at_1,
          variant_id: cell.variant_id,
          actual_semantic_steps: cell.actual_semantic_steps,
          metrics: {
            at1: formatAccuracyCell(cell, "at1"),
            at5: formatAccuracyCell(cell, "at5"),
            at10: formatAccuracyCell(cell, "at10"),
            mrr: formatAccuracyCell(cell, "mrr"),
            mean_rank: formatAccuracyCell(cell, "mean_rank"),
          },
        }];
      })),
    };
  });
  const eligibleCompleted = runLevelResults.filter((record) => record.included_in_accuracy);
  const generatedAt = new Date().toISOString();
  return {
    schema_version: ACCURACY_SCHEMA_VERSION,
    experiment_config: {
      agent_id: "mini-swe-gpt56",
      agent: "mini-swe-agent",
      model: "gpt-5.6",
      protocol_version: FROZEN_PROMPT_VERSION,
      prompt_hash: FROZEN_PROMPT_HASH,
      target_runs: targetRuns,
      depths: ACCURACY_DEPTHS,
    },
    summary: {
      total_historical_runs: runLevelResults.length,
      eligible_completed_runs: eligibleCompleted.length,
      excluded_runs: runLevelResults.length - eligibleCompleted.length,
      missing_repetitions_count_as_failures: false,
    },
    matrix: { model: "gpt-5.6", agent: "mini-swe-agent", depths: ACCURACY_DEPTHS, rows },
    depth_summary: aggregated.depthSummary.map(statisticalRow),
    family_summary: aggregated.familySummary.map((family) => ({
      family: family.family,
      project: family.project,
      bug_id: family.bug_id,
      original: statisticalRow(family.original),
      depths: family.depths.map(statisticalRow),
    })),
    cohort_summaries: {
      seven_family_pilot: {
        cohort_id: "seven-family-l10-l90-v1",
        families: SEVEN_FAMILY_PILOT_FAMILIES.map((family) => familyId(family.project, family.bug_id)),
        original: statisticalRow({ depth: "Original", ...aggregateAcrossCells(pilotAggregated.originals) }),
        depths: pilotAggregated.depthSummary.map(statisticalRow),
      },
    },
    run_level_results: runLevelResults,
    generated_at: generatedAt,
  };
}

async function atomicWrite(filePath, content) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const temporary = `${filePath}.tmp-${process.pid}`;
  await fs.writeFile(temporary, content, { mode: 0o600 });
  await fs.rename(temporary, filePath);
}

export async function writeAccuracyAnalysis(options) {
  const analysis = await buildAccuracyAnalysis(options);
  const outputDir = path.join(options.benchmarkRoot, "analysis", "accuracy");
  const matrixRows = analysis.matrix.rows.map((row) => ({
    family: row.family,
    ...Object.fromEntries(ACCURACY_DEPTHS.flatMap((depth) => {
      const cell = row.cells[depth];
      return [
        [`${depth}_accuracy_at_1`, cell.accuracy_at_1],
        [`${depth}_n`, cell.n_eligible],
        [`${depth}_target_runs`, cell.target_runs],
        [`${depth}_availability`, cell.availability],
      ];
    })),
  }));
  const runRows = analysis.run_level_results.map((run) => ({
    model: run.model,
    agent: run.agent,
    agent_id: run.agent_id,
    family: run.family,
    project: run.project,
    bug_id: run.bug_id,
    task_type: run.task_type,
    variant_id: run.variant_id,
    depth: run.depth,
    run_id: run.run_id,
    gold_rank: run.gold_rank,
    hit_at_1: run.hit_at_1,
    hit_at_5: run.hit_at_5,
    hit_at_10: run.hit_at_10,
    reciprocal_rank: run.reciprocal_rank,
    status: run.status,
    eligible: run.eligible,
    included_in_accuracy: run.included_in_accuracy,
    eligibility_reasons: run.eligibility_reasons,
    protocol_version: run.protocol_version,
    prompt_hash: run.prompt_hash,
    started_at: run.started_at,
    completed_at: run.completed_at,
    duration_ms: run.duration_ms,
    artifact_path: run.artifact_path,
  }));
  await Promise.all([
    atomicWrite(path.join(outputDir, "accuracy_matrix.csv"), rowsToCsv(matrixRows)),
    atomicWrite(path.join(outputDir, "accuracy_by_depth.csv"), rowsToCsv(analysis.depth_summary)),
    atomicWrite(path.join(outputDir, "accuracy_by_family.csv"), rowsToCsv(analysis.family_summary.flatMap((family) => [family.original, ...family.depths]))),
    atomicWrite(path.join(outputDir, "run_level_results.csv"), rowsToCsv(runRows)),
    atomicWrite(path.join(outputDir, "aggregation.json"), `${JSON.stringify(analysis, null, 2)}\n`),
    atomicWrite(path.join(outputDir, "aggregation_report.md"), accuracyReport(analysis)),
  ]);
  return { analysis, outputDir };
}
