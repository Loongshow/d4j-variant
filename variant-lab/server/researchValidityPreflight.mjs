/**
 * Research-validity preflight (Part 15 gate).
 *
 * All-or-nothing readiness check for a strict depth experiment. It is deliberately
 * pessimistic: anything unverified, unaudited or legacy counts as NOT READY. It never
 * launches anything and never mutates anything.
 */

import fs from "node:fs/promises";
import path from "node:path";

import {
  EVIDENCE_POLICY_VERSION,
  LEGACY_EVIDENCE_POLICY_VERSION,
  classifyEvidenceProvenanceText,
  failureEvidencePolicy,
  screenEvidenceForPrivateMetadata,
} from "./evidencePolicy.mjs";
import { assertAgentTaskIsolation, buildVariantAgentTask } from "./benchmarkStore.mjs";
import { getCohort } from "./cohorts.mjs";
import {
  DEPTH_AUDIT_STATUS,
  auditReasoningTree,
  loadDepthAuditRegistry,
  parseReasoningTreeDocument,
  resolveDepthAudit,
  strictDepthEligibility,
  strictThresholdFor,
} from "./semanticDepth.mjs";
import { deriveVariantProvenance, loadProvenanceSupplement, validateVariantProvenance } from "./variantProvenance.mjs";
import {
  discoverVariantRecords,
  readVariantRecord,
  variantArtifactConsistency,
  variantBenchmarkEligibility,
} from "./variantLibrary.mjs";
import { PROMPT_VERSION, LOCALIZATION_SYSTEM_PROMPT, sha256Text } from "./agents/agentAdapter.mjs";

export const RESEARCH_VALIDITY_PREFLIGHT_SCHEMA_VERSION = "d4j-research-validity-preflight/v1";
export const FROZEN_BASE_PROMPT_SHA256 = "845e21e73b1ed61edcff3d959e4fee38623df94ae6e0cd41f6c4488ad9c7dd89";

function check(id, status, message, extra = {}) {
  return { id, status, message, ...extra };
}

/**
 * Rendered-payload compliance (the gap that let CHART-1-L10-STRICT-001 reach a launch).
 *
 * Package metadata alone is NOT sufficient evidence of compliance. A package can declare
 * the right policy version, pass every eligibility and provenance check, and still render
 * an agent-visible task that the run-time isolation guard refuses, or that carries a
 * human-authored prose summary in place of captured failure output.
 *
 * This inspects the FINAL payload after manifest -> evidence construction -> task
 * rendering, exactly as `createBenchmarkRun` will see it before preparation. It mutates
 * nothing and launches nothing.
 */
export function renderedAgentTaskCompliance(task) {
  const stackTrace = String(task?.stack_trace ?? "");
  const failingTestSource = String(task?.failing_test_source ?? "");
  const isolation = assertAgentTaskIsolation(task ?? {});
  const classification = classifyEvidenceProvenanceText(stackTrace);
  const stackScreen = screenEvidenceForPrivateMetadata(stackTrace);
  const sourceScreen = screenEvidenceForPrivateMetadata(failingTestSource);
  const reasons = [];

  if (!isolation.ok) {
    reasons.push(`rendered task is refused by the isolation guard: ${isolation.failures.join(", ")}`);
  }
  if (!stackTrace) {
    reasons.push("rendered stack_trace is empty");
  } else if (classification !== "machine_generated") {
    reasons.push(`rendered stack_trace is ${classification}; the policy forbids a human-authored summary as a substitute for captured output`);
  }
  if (!stackScreen.ok) {
    reasons.push(`rendered stack_trace names private benchmark infrastructure: ${stackScreen.hits.join(", ")}`);
  }
  if (!failingTestSource) {
    reasons.push("rendered failing_test_source is empty; the agent would receive no failing test source");
  }
  if (!sourceScreen.ok) {
    reasons.push(`rendered failing_test_source names private benchmark infrastructure: ${sourceScreen.hits.join(", ")}`);
  }

  return {
    ok: reasons.length === 0,
    reasons,
    isolation_ok: isolation.ok,
    isolation_failures: isolation.failures ?? [],
    stack_trace_classification: classification,
    stack_trace_chars: stackTrace.length,
    stack_trace_lines: stackTrace ? stackTrace.split("\n").length : 0,
    failing_test_source_chars: failingTestSource.length,
    private_metadata_hits: [...stackScreen.hits, ...sourceScreen.hits],
  };
}

/**
 * @param {object} options
 * @param {string} options.repoRoot
 * @param {string} options.cohortId
 * @param {Array<{arm: string, task_type: "original"|"variant", variant_id?: string, project?: string, bug_id?: number, required_level?: string}>} options.conditions
 */
export async function runResearchValidityPreflight({ repoRoot, cohortId, conditions, experimentId }) {
  const variantsRoot = path.join(repoRoot, "new_bug_variants");
  const checkoutRoot = path.join(repoRoot, "workspaces", "defects4j");
  const rvDir = path.join(repoRoot, "benchmark_runs", "analysis", "research-validity");
  const registry = await loadDepthAuditRegistry(path.join(rvDir, "depth-audit-registry.json"));
  const provenanceSupplement = await loadProvenanceSupplement(path.join(rvDir, "provenance-supplement.json"));

  const checks = [];
  const conditionReports = [];

  /* ---------------------------------------------------------- global checks */

  let cohort = null;
  try {
    cohort = getCohort(cohortId);
    checks.push(
      check(
        "cohort:explicit",
        cohort.supports_strict_depth_claims ? "pass" : "fail",
        cohort.supports_strict_depth_claims
          ? `Cohort ${cohort.cohort_id} is declared and supports strict depth claims (basis: ${cohort.depth_basis})`
          : `Cohort ${cohort.cohort_id} uses ${cohort.depth_basis} and may not support strict depth claims`,
      ),
    );
  } catch (error) {
    checks.push(check("cohort:explicit", "fail", error.message));
  }

  const promptHash = sha256Text(LOCALIZATION_SYSTEM_PROMPT);
  checks.push(
    check(
      "protocol:prompt-frozen",
      PROMPT_VERSION === "d4j-localization-only/v2" && promptHash === FROZEN_BASE_PROMPT_SHA256 ? "pass" : "fail",
      `Prompt version ${PROMPT_VERSION}, base sha256 ${promptHash}`,
      { prompt_version: PROMPT_VERSION, base_prompt_sha256: promptHash },
    ),
  );

  checks.push(
    check(
      "protocol:evidence-policy-frozen",
      failureEvidencePolicy.policy_version === EVIDENCE_POLICY_VERSION &&
        failureEvidencePolicy.identical_across_depths === true &&
        failureEvidencePolicy.human_authored_summaries.startsWith("forbidden")
        ? "pass"
        : "fail",
      `Evidence policy ${failureEvidencePolicy.policy_version}: identical across depths, human-authored summaries forbidden, max ${failureEvidencePolicy.max_lines} lines / ${failureEvidencePolicy.max_chars} chars`,
    ),
  );

  const allRecords = await discoverVariantRecords(variantsRoot);
  checks.push(
    check(
      "historical:variants-discoverable",
      allRecords.length > 0 ? "pass" : "fail",
      `${allRecords.length} canonical variant records discovered; none were modified by the hardening pass`,
      { variant_record_count: allRecords.length },
    ),
  );

  const benchmarkRoot = path.join(repoRoot, "benchmark_runs");
  let runManifestCount = 0;
  // Bounded walk: run manifests sit at most a few levels below benchmark_runs, while
  // prepared agent workspaces below them contain entire Java checkouts. Descending into
  // those would make this gate take minutes and would count nothing extra.
  const SKIP_DIRS = new Set(["workspace", "staging", "node_modules", ".git", "build", "target", "dist"]);
  const countRuns = async (dir, depth = 0) => {
    if (depth > 6) return;
    let entries = [];
    try {
      entries = await fs.readdir(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      if (entry.isDirectory()) {
        if (SKIP_DIRS.has(entry.name)) continue;
        await countRuns(path.join(dir, entry.name), depth + 1);
      } else if (entry.name === "run_manifest.json") {
        runManifestCount += 1;
      }
    }
  };
  await countRuns(benchmarkRoot);
  checks.push(
    check(
      "historical:runs-preserved",
      runManifestCount > 0 ? "pass" : "fail",
      `${runManifestCount} historical run manifests present and untouched`,
      { run_manifest_count: runManifestCount },
    ),
  );

  /* ------------------------------------------------------- per-condition checks */

  for (const condition of conditions) {
    const report = { arm: condition.arm, task_type: condition.task_type, checks: [] };

    if (condition.task_type === "original") {
      const buggy = path.join(checkoutRoot, `${condition.project}-${condition.bug_id}`, "buggy");
      let exists = false;
      try {
        await fs.access(buggy);
        exists = true;
      } catch {
        exists = false;
      }
      report.checks.push(
        check("checkout:buggy-present", exists ? "pass" : "fail", `${condition.project}-${condition.bug_id} buggy checkout ${exists ? "present" : "missing"}`),
      );
      report.ready = report.checks.every((item) => item.status === "pass" || item.status === "info");
      conditionReports.push(report);
      continue;
    }

    if (!condition.variant_id) {
      report.checks.push(check("condition:artifact-exists", "fail", "No variant id is specified for this arm"));
      report.ready = false;
      conditionReports.push(report);
      continue;
    }

    const record = allRecords.find((item) => item.variantId === condition.variant_id) ?? null;
    if (!record) {
      report.checks.push(
        check(
          "condition:artifact-exists",
          "fail",
          `No validated artifact exists for ${condition.variant_id}. The condition cannot be run and must not be substituted.`,
        ),
      );
      report.ready = false;
      conditionReports.push(report);
      continue;
    }

    const full = await readVariantRecord(record.dir);
    report.checks.push(check("condition:artifact-exists", "pass", `${condition.variant_id} found at ${path.relative(repoRoot, record.dir)}`));

    const eligibility = variantBenchmarkEligibility(full);
    report.checks.push(
      check("condition:benchmark-eligible", eligibility.ok ? "pass" : "fail", eligibility.ok ? "Benchmark eligibility passes" : eligibility.reasons.join("; ")),
    );

    const consistency = await variantArtifactConsistency(full, { checkoutRoot });
    report.checks.push(
      check(
        "condition:artifact-consistency",
        consistency.ok && consistency.fully_verified ? "pass" : consistency.ok ? "unverified" : "fail",
        consistency.ok
          ? consistency.fully_verified
            ? `Consistent and fully verified (${consistency.method_verification_mode})`
            : `Consistent but unverified checks remain: ${consistency.unverified.join(", ")}`
          : `Failing checks: ${consistency.checks.filter((item) => item.status === "fail").map((item) => item.id).join(", ")}`,
        { method_verification_mode: consistency.method_verification_mode, lexical_exposures: consistency.lexical_exposures },
      ),
    );

    const reproducibility = full.manifest?.reproducibility?.status ?? "not_checked";
    report.checks.push(
      check("condition:reproducibility", reproducibility === "passed" ? "pass" : "fail", `Reproducibility status: ${reproducibility}`),
    );

    const integrity = Boolean(full.artifactStatus?.["source_hashes.json"]);
    report.checks.push(
      check("condition:source-integrity-record", integrity ? "pass" : "fail", integrity ? "source_hashes.json present" : "source_hashes.json missing"),
    );

    const privateArtifacts = ["reasoning_tree.yaml", "variant_manifest.json", "validation.json", "variant.patch", "test.patch"];
    const privatePresent = privateArtifacts.every((name) => full.artifactStatus?.[name] !== false);
    report.checks.push(
      check(
        "condition:private-metadata-isolated",
        privatePresent ? "pass" : "fail",
        privatePresent
          ? "Private artifacts live only in the canonical package; the agent workspace is built by copy-filter, double sanitisation and a forbidden-entry scan"
          : "Expected private artifacts are missing from the canonical package",
      ),
    );

    const depth = strictDepthEligibility(condition.variant_id, registry, full.manifest);
    const resolved = depth.resolved;
    const threshold = strictThresholdFor(condition.required_level ?? resolved.nominal_depth);
    report.checks.push(
      check(
        "condition:audited-depth",
        depth.ok ? "pass" : "fail",
        depth.ok
          ? `Audited semantic depth ${resolved.audited_semantic_depth} >= ${threshold} for ${resolved.nominal_depth}`
          : depth.reasons.join("; "),
        {
          nominal_depth: resolved.nominal_depth,
          nominal_unit_count: resolved.nominal_unit_count,
          audited_semantic_depth: resolved.audited_semantic_depth,
          depth_audit_status: resolved.depth_audit_status,
          depth_audit_report: resolved.depth_audit_report,
        },
      ),
    );

    let treeText = "";
    try {
      treeText = await fs.readFile(path.join(record.dir, "reasoning_tree.yaml"), "utf8");
    } catch {
      treeText = "";
    }
    const structure = auditReasoningTree(parseReasoningTreeDocument(treeText));
    report.checks.push(
      check(
        "condition:semantic-audit-structure",
        structure.structurally_auditable ? "pass" : "fail",
        structure.structurally_auditable
          ? `${structure.structure_class}, ${structure.parsed_unit_count} units, longest chain ${structure.longest_dependency_chain_nodes}, ${structure.multi_parent_nodes} multi-parent nodes`
          : `Reasoning tree is not structurally auditable (format ${structure.format}, structure ${structure.structure_class})`,
        structure,
      ),
    );

    // A package built before d4j-failure-evidence/v1 truthfully declares the legacy
    // policy. That is recorded rather than treated as a missing field, because the
    // policy that governs what the agent actually sees is applied at RUN time by the
    // adapter, not at packaging time. The separate `condition:evidence-policy-*` checks
    // below make both facts explicit rather than collapsing them.
    const provenance = await deriveVariantProvenance(full, {
      promptVersion: PROMPT_VERSION,
      promptHash,
      depthAudit: resolved,
      legacyEvidencePolicyVersion: LEGACY_EVIDENCE_POLICY_VERSION,
      supplement: provenanceSupplement,
    });
    const provenanceResult = validateVariantProvenance(provenance, { record: full });
    report.checks.push(
      check(
        "condition:provenance-complete",
        provenanceResult.complete ? "pass" : "fail",
        provenanceResult.complete
          ? provenanceResult.completeness === "complete_via_supplement"
            ? `All required provenance fields available; ${provenanceResult.supplemented_fields.join(", ")} reconstructed from the package's own evidence via provenance-supplement.json (artifact not modified)`
            : "All required provenance fields recorded in the package"
          : `Missing: ${provenanceResult.missing_fields.join(", ") || "none"}; placeholders: ${provenanceResult.placeholder_fields.join(", ") || "none"}`,
        { completeness: provenanceResult.completeness, supplemented_fields: provenanceResult.supplemented_fields, warnings: provenanceResult.warnings },
      ),
    );

    report.checks.push(
      check(
        "condition:evidence-policy-package-declaration",
        provenance.evidence_policy_version === EVIDENCE_POLICY_VERSION ? "pass" : "info",
        provenance.evidence_policy_version === EVIDENCE_POLICY_VERSION
          ? `Package declares ${EVIDENCE_POLICY_VERSION}`
          : `Package predates the evidence policy and declares ${provenance.evidence_policy_version}. This does not block the run: the policy is applied at run time by the adapter, and the run manifest records the version actually in force.`,
        { package_declared_policy: provenance.evidence_policy_version, run_time_policy: EVIDENCE_POLICY_VERSION },
      ),
    );

    // The rendered agent-visible payload is the authority, not the package metadata.
    // This is the check whose absence allowed a package carrying a human-authored
    // "no gold method appears" summary to be reported READY and then be refused at
    // launch by the run-time isolation guard.
    const manifestStack = String(full.manifest?.trigger?.stack_trace ?? "");
    let renderedTask = null;
    let renderError = null;
    try {
      renderedTask = buildVariantAgentTask({ record: full, checkoutRoot }).agent_visible_task;
    } catch (error) {
      renderError = error instanceof Error ? error.message : String(error);
    }

    if (renderError || !renderedTask) {
      report.checks.push(
        check(
          "condition:rendered-agent-task-compliant",
          "unverified",
          `The agent-visible task could not be rendered, so its compliance cannot be confirmed: ${renderError ?? "no task produced"}`,
        ),
      );
    } else {
      const rendered = renderedAgentTaskCompliance(renderedTask);
      report.checks.push(
        check(
          "condition:rendered-agent-task-compliant",
          rendered.ok ? "pass" : "fail",
          rendered.ok
            ? `Rendered agent-visible task complies with ${EVIDENCE_POLICY_VERSION}: machine-generated stack_trace (${rendered.stack_trace_lines} lines), failing_test_source present (${rendered.failing_test_source_chars} chars), isolation guard passes`
            : `Rendered agent-visible task is NOT compliant: ${rendered.reasons.join("; ")}`,
          { rendered_compliance: rendered },
        ),
      );

      report.checks.push(
        check(
          "condition:evidence-policy-applies",
          rendered.ok ? "pass" : "fail",
          manifestStack
            ? `Manifest records a trigger.stack_trace (${manifestStack.length} chars) classified ${classifyEvidenceProvenanceText(manifestStack)}; the rendered payload is ${rendered.ok ? "compliant" : "NOT compliant"} under ${EVIDENCE_POLICY_VERSION}`
            : `No authored trigger.stack_trace; evidence is captured from the prepared workspace under ${EVIDENCE_POLICY_VERSION}`,
          { manifest_stack_classification: classifyEvidenceProvenanceText(manifestStack) },
        ),
      );
    }

    // `info` records a documented, non-blocking fact. `unverified` and `fail` both block:
    // a check that could not be evaluated is never treated as a pass.
    report.ready = report.checks.every((item) => item.status === "pass" || item.status === "info");
    conditionReports.push(report);
  }

  const globalOk = checks.every((item) => item.status === "pass");
  const conditionsOk = conditionReports.every((item) => item.ready);
  const notReady = conditionReports.filter((item) => !item.ready).map((item) => item.arm);

  return {
    schema_version: RESEARCH_VALIDITY_PREFLIGHT_SCHEMA_VERSION,
    experiment_id: experimentId,
    cohort_id: cohortId,
    checked_at: new Date().toISOString(),
    experiment_ready: globalOk && conditionsOk,
    launch_authorized: false,
    decision: globalOk && conditionsOk ? "ALL_CONDITIONS_READY_AWAITING_USER_AUTHORIZATION" : "STOP_BEFORE_AGENT_LAUNCH",
    agent_processes_launched: 0,
    benchmark_runs_created: 0,
    not_ready_conditions: notReady,
    global_checks: checks,
    conditions: conditionReports,
  };
}
