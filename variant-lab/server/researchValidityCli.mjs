#!/usr/bin/env node
/**
 * Read-only research-validity preflight runner.
 *
 * Launches nothing. Writes one JSON report under
 * benchmark_runs/analysis/research-validity/ and prints a summary.
 *
 *   node server/researchValidityCli.mjs [--experiment=<id>] [--out=<path>]
 */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { runResearchValidityPreflight } from "./researchValidityPreflight.mjs";
import { STRICT_EXPERIMENT_CONDITIONS, STRICT_EXPERIMENT_COHORT_ID, STRICT_EXPERIMENT_ID } from "./strictExperiment.mjs";

const moduleDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(moduleDir, "..", "..");

function argValue(name, fallback) {
  const prefix = `--${name}=`;
  const match = process.argv.find((argument) => argument.startsWith(prefix));
  return match ? match.slice(prefix.length) : fallback;
}

const experimentId = argValue("experiment", STRICT_EXPERIMENT_ID);
const report = await runResearchValidityPreflight({
  repoRoot,
  cohortId: STRICT_EXPERIMENT_COHORT_ID,
  conditions: STRICT_EXPERIMENT_CONDITIONS,
  experimentId,
});

const defaultOut = path.join(
  repoRoot,
  "benchmark_runs",
  "analysis",
  "research-validity",
  `preflight-${experimentId}.json`,
);
const outPath = path.resolve(argValue("out", defaultOut));
await fs.mkdir(path.dirname(outPath), { recursive: true });
await fs.writeFile(outPath, `${JSON.stringify(report, null, 2)}\n`);

console.log(`Research-validity preflight: ${experimentId}`);
console.log(`Cohort: ${report.cohort_id}`);
console.log("");
for (const item of report.global_checks) {
  console.log(`  [${item.status.toUpperCase().padEnd(10)}] ${item.id} - ${item.message}`);
}
console.log("");
for (const condition of report.conditions) {
  console.log(`  ${condition.arm}: ${condition.ready ? "READY" : "NOT READY"}`);
  for (const item of condition.checks) {
    if (item.status !== "pass") console.log(`      [${item.status.toUpperCase()}] ${item.id} - ${item.message}`);
  }
}
console.log("");
console.log(`EXPERIMENT READY: ${report.experiment_ready ? "YES" : "NO"}`);
if (!report.experiment_ready) console.log(`Not ready: ${report.not_ready_conditions.join(", ") || "see global checks"}`);
console.log(`Decision: ${report.decision}`);
console.log(`Agent processes launched: ${report.agent_processes_launched}`);
console.log(`Report: ${path.relative(repoRoot, outPath)}`);
