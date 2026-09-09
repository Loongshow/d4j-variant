import path from "node:path";
import { fileURLToPath } from "node:url";
import { writeAccuracyAnalysis } from "./accuracyStore.mjs";

const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = path.resolve(appRoot, "..");
const benchmarkRoot = path.join(repoRoot, "benchmark_runs");
const { analysis, outputDir } = await writeAccuracyAnalysis({ benchmarkRoot, repoRoot });

process.stdout.write(`${JSON.stringify({
  status: "exported",
  artifact_path: `${path.relative(repoRoot, outputDir)}/`,
  total_historical_runs: analysis.summary.total_historical_runs,
  eligible_completed_runs: analysis.summary.eligible_completed_runs,
  excluded_runs: analysis.summary.excluded_runs,
}, null, 2)}\n`);
