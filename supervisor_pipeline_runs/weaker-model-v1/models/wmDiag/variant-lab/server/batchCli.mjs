import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  DEFAULT_BATCH_ID,
  checkpointBatchEntry,
  ensureBatch,
  nextBatchEntry,
  readBatch,
  writeBatchOutputs,
} from "./batchStore.mjs";
import { verifyOriginalBug } from "./originalVerification.mjs";

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(appRoot, "..");
const benchmarkRoot = path.join(repoRoot, "benchmark_runs");
const checkoutRoot = path.join(repoRoot, "workspaces", "defects4j");
const args = process.argv.slice(2);
const command = args.find((arg) => !arg.startsWith("--")) ?? "status";
const batchIdArg = args.find((arg) => arg.startsWith("--batch="));
const batchId = batchIdArg ? batchIdArg.slice("--batch=".length) : DEFAULT_BATCH_ID;

function heartbeat(message) {
  process.stdout.write(`[${new Date().toISOString()}] ${message}\n`);
}

function relativeArtifact(absolute) {
  return `${path.relative(repoRoot, absolute).split(path.sep).join("/")}/`;
}

async function resumeOriginals() {
  await ensureBatch(benchmarkRoot, batchId);
  while (true) {
    const { manifest } = await readBatch(benchmarkRoot, batchId);
    const pending = (manifest.originals ?? []).find((entry) => ["pending", "running"].includes(entry.status));
    if (!pending) break;
    const key = pending.key;
    await checkpointBatchEntry(benchmarkRoot, batchId, key, {
      current_stage: "verify_original",
      status: "running",
      resume_from: "verify_original",
      failure_reason: null,
    });
    try {
      const { record, artifactDir } = await verifyOriginalBug({
        repoRoot,
        checkoutRoot,
        batchDir: path.join(benchmarkRoot, "batches", batchId),
        project: pending.project,
        heartbeat,
      });
      await checkpointBatchEntry(benchmarkRoot, batchId, key, {
        current_stage: "benchmark_original",
        status: "verified",
        resume_from: "benchmark_original",
        task_id: record.task_id,
        semantic_inference_steps: record.reasoning.semantic_inference_steps,
        shortest_reasoning_path: record.reasoning.shortest_reasoning_path,
        reasoning_level_status: record.reasoning.reasoning_level_status,
        root_cause: record.semantic_root_cause,
        gold_methods: record.gold_methods,
        gold_method: record.gold_methods.map((item) => `${item.class}::${item.method}`).join("; "),
        artifact_paths: [relativeArtifact(artifactDir)],
        failure_reason: null,
      });
      heartbeat(`${pending.project}-1 original verification complete`);
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      await checkpointBatchEntry(benchmarkRoot, batchId, key, {
        current_stage: "verify_original",
        status: "environment_blocked",
        resume_from: "verify_original",
        failure_reason: reason,
      });
      heartbeat(`${pending.project}-1 original verification blocked: ${reason}`);
    }
  }
  await writeBatchOutputs(benchmarkRoot, batchId);
}

async function printStatus() {
  const { dir, manifest } = await ensureBatch(benchmarkRoot, batchId);
  const next = nextBatchEntry(manifest);
  const originalCounts = Object.groupBy(manifest.originals ?? [], (entry) => entry.status);
  const variantCounts = Object.groupBy(manifest.variants ?? [], (entry) => entry.status);
  process.stdout.write(
    `${JSON.stringify(
      {
        batch_id: manifest.batch_id,
        status: manifest.status,
        path: relativeArtifact(dir),
        next: next?.key ?? null,
        original_statuses: Object.fromEntries(Object.entries(originalCounts).map(([key, value]) => [key, value.length])),
        variant_statuses: Object.fromEntries(Object.entries(variantCounts).map(([key, value]) => [key, value.length])),
      },
      null,
      2,
    )}\n`,
  );
}

async function resumeFullBatch() {
  const port = Number(process.env.D4J_API_PORT ?? 8787);
  const response = await fetch(`http://127.0.0.1:${port}/api/benchmark-batches/${encodeURIComponent(batchId)}/resume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error ?? `${response.status} ${response.statusText}`);
  process.stdout.write(`${JSON.stringify(body, null, 2)}\n`);
}

if (command === "init") {
  await ensureBatch(benchmarkRoot, batchId);
  await writeBatchOutputs(benchmarkRoot, batchId);
  await printStatus();
} else if (command === "resume-originals") {
  await resumeOriginals();
  await printStatus();
} else if (command === "export") {
  await ensureBatch(benchmarkRoot, batchId);
  await writeBatchOutputs(benchmarkRoot, batchId);
  await printStatus();
} else if (command === "resume") {
  await resumeFullBatch();
} else if (command === "status") {
  await printStatus();
} else {
  throw new Error(`Unknown batch command: ${command}`);
}
