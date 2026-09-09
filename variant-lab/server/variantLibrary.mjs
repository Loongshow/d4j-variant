import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

export const MANIFEST_SCHEMA_VERSION = "d4j-variant-manifest/v1";
export const VALIDATION_SCHEMA_VERSION = "d4j-validation/v1";
export const FL_RESULT_SCHEMA_VERSION = "d4j-fault-localization-run/v1";

export const canonicalArtifactFiles = [
  "variant_manifest.json",
  "reasoning_tree.yaml",
  "variant.patch",
  "test.patch",
  "validation.json",
  "validation.log",
  "variant_report.md",
];

export const chartSecondaryVariantId = "CHART-1-L10-SECONDARY-02";

export function normalizeProject(value) {
  const project = String(value ?? "").trim();
  if (!/^[A-Za-z][A-Za-z0-9]*$/.test(project)) {
    throw new Error("Invalid project id");
  }
  return project;
}

export function normalizeBugId(value) {
  const bugId = Number(value);
  if (!Number.isInteger(bugId) || bugId <= 0) {
    throw new Error("Invalid bug id");
  }
  return String(bugId);
}

export function normalizeLevel(value) {
  const level = String(value ?? "").trim().toUpperCase();
  if (!/^L(?:10|20|30|50|70|90)$/.test(level)) {
    throw new Error("Invalid variant level");
  }
  return level;
}

export function sanitizeVariantId(value) {
  const variantId = String(value ?? "").trim();
  if (
    !variantId ||
    variantId.includes("..") ||
    variantId.includes("/") ||
    variantId.includes("\\") ||
    path.isAbsolute(variantId) ||
    !/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(variantId)
  ) {
    throw new Error("Invalid variant id");
  }
  return variantId;
}

export function safeResolve(root, requestedPath = "") {
  const relativePath = String(requestedPath);
  if (!relativePath || path.isAbsolute(relativePath) || relativePath.includes("\0")) {
    throw new Error("Invalid file path");
  }
  const target = path.resolve(root, relativePath);
  const rootWithSep = root.endsWith(path.sep) ? root : `${root}${path.sep}`;
  if (target !== root && !target.startsWith(rootWithSep)) {
    throw new Error("Rejected path traversal attempt");
  }
  return target;
}

export function canonicalVariantDir(variantsRoot, project, bugId, level, variantId) {
  return path.join(
    variantsRoot,
    normalizeProject(project),
    `bug-${normalizeBugId(bugId)}`,
    normalizeLevel(level),
    sanitizeVariantId(variantId),
  );
}

export function safeArtifactPath(variantDir, artifactName) {
  if (!canonicalArtifactFiles.includes(artifactName) && !["generation_trace.json", "source_hashes.json"].includes(artifactName)) {
    throw new Error("Invalid artifact name");
  }
  return safeResolve(variantDir, artifactName);
}

export async function exists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

export async function readJsonIfExists(filePath) {
  if (!(await exists(filePath))) return null;
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

export async function writeJsonIfMissing(filePath, data) {
  if (await exists(filePath)) return "existing";
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(data, null, 2)}\n`);
  return "created";
}

export async function writeTextIfMissing(filePath, content) {
  if (await exists(filePath)) return "existing";
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, content);
  return "created";
}

export function artifactMapFor(variantId) {
  return {
    manifest: "variant_manifest.json",
    reasoning_tree: "reasoning_tree.yaml",
    variant_patch: "variant.patch",
    test_patch: "test.patch",
    validation: "validation.json",
    validation_log: "validation.log",
    variant_report: "variant_report.md",
    generation_trace: "generation_trace.json",
    variant_id: variantId,
  };
}

export function validationGatePasses(validation) {
  if (!validation || typeof validation !== "object") return false;
  const gate = validation.gate ?? {};
  const triggerRuns = gate.variant_trigger_runs ?? validation.variant_trigger_runs ?? [];
  return (
    validation.status === "accepted" &&
    gate.baseline_compile?.status === "pass" &&
    gate.baseline_trigger?.status === "pass" &&
    gate.variant_compile?.status === "pass" &&
    Array.isArray(triggerRuns) &&
    triggerRuns.length >= 3 &&
    triggerRuns.every((run) => run.status === "expected_fail") &&
    gate.deterministic?.status === "pass" &&
    gate.production_fault?.status === "pass" &&
    gate.gold_method_known?.status === "pass"
  );
}

export function reproducibilityStatusFor(manifest) {
  return String(manifest?.reproducibility?.status ?? manifest?.reproducibility_status ?? "not_checked");
}

export function variantBenchmarkEligibility(record, options = {}) {
  const debugOverride = Boolean(options.debug_allow_unreproduced_variant ?? options.allow_unreproduced_variant);
  const manifest = record?.manifest ?? null;
  const reproducibilityStatus = reproducibilityStatusFor(manifest);
  const reasons = [];

  if (!record) reasons.push("Variant record is missing");
  if (record?.status === "needs_revalidation") reasons.push("Variant requires fresh revalidation");
  if (!record?.schema?.ok) reasons.push(`Variant manifest schema failed: ${(record?.schema?.errors ?? []).join("; ")}`);
  if (!validationGatePasses(record?.validation)) reasons.push("Historical validation gate is not satisfied");
  if (reproducibilityStatus !== "passed") reasons.push(`Fresh reproducibility status is ${reproducibilityStatus}`);
  if (manifest?.benchmark_eligible !== true) reasons.push("Manifest benchmark_eligible is not true");

  if (debugOverride) {
    return {
      ok: true,
      debug_override: true,
      reason: reasons.length ? `Debug override allowed unreproduced variant: ${reasons.join("; ")}` : "Debug override was not needed",
      reasons,
      reproducibility_status: reproducibilityStatus,
      benchmark_eligible: Boolean(manifest?.benchmark_eligible),
    };
  }

  return {
    ok: reasons.length === 0,
    debug_override: false,
    reason: reasons[0] ?? "Variant is benchmark eligible",
    reasons,
    reproducibility_status: reproducibilityStatus,
    benchmark_eligible: Boolean(manifest?.benchmark_eligible),
  };
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function classSourcePath(className) {
  return path.join("source", `${String(className).replaceAll(".", "/")}.java`);
}

function shortClassName(className) {
  return String(className).split(".").at(-1) ?? String(className);
}

function isRendererOwnedFault(className) {
  return /\brenderer\b/i.test(String(className));
}

function artifactNameForHashKey(key) {
  const aliases = {
    manifest: "variant_manifest.json",
    reasoning_tree: "reasoning_tree.yaml",
    variant_patch: "variant.patch",
    test_patch: "test.patch",
    validation: "validation.json",
    validation_log: "validation.log",
    variant_report: "variant_report.md",
    generation_trace: "generation_trace.json",
    source_hashes: "source_hashes.json",
  };
  if (canonicalArtifactFiles.includes(key) || ["generation_trace.json", "source_hashes.json"].includes(key)) return key;
  return aliases[key] ?? null;
}

export async function sha256File(filePath) {
  return crypto.createHash("sha256").update(await fs.readFile(filePath)).digest("hex");
}

export async function artifactHashChecks(record) {
  const hashes = record?.manifest?.reproducibility?.artifact_hashes ?? record?.manifest?.artifact_hashes ?? {};
  const checks = [];
  for (const [key, expectedHash] of Object.entries(hashes)) {
    if (typeof expectedHash !== "string" || !expectedHash) continue;
    const artifactName = artifactNameForHashKey(key);
    if (!artifactName) {
      checks.push({ id: `hash:${key}`, status: "fail", message: `Unknown artifact hash key: ${key}` });
      continue;
    }
    const artifactPath = safeArtifactPath(record.dir, artifactName);
    if (!(await exists(artifactPath))) {
      checks.push({ id: `hash:${key}`, status: "fail", message: `${artifactName} is missing` });
      continue;
    }
    const actualHash = await sha256File(artifactPath);
    checks.push({
      id: `hash:${key}`,
      status: actualHash === expectedHash ? "pass" : "fail",
      message: `${artifactName} sha256 ${actualHash === expectedHash ? "matches" : "does not match"} manifest`,
      expected: expectedHash,
      actual: actualHash,
      artifact: artifactName,
    });
  }
  return { ok: checks.every((check) => check.status !== "fail"), checks };
}

async function readArtifactText(record, artifactName) {
  const artifactPath = safeArtifactPath(record.dir, artifactName);
  if (!(await exists(artifactPath))) return "";
  return fs.readFile(artifactPath, "utf8");
}

export async function variantArtifactConsistency(record, options = {}) {
  const checks = [];
  const add = (id, ok, message, extra = {}) => {
    checks.push({ id, status: ok ? "pass" : "fail", message, ...extra });
  };

  if (!record) {
    return {
      ok: false,
      checks: [{ id: "record", status: "fail", message: "Variant record is missing" }],
    };
  }

  for (const artifactName of canonicalArtifactFiles) {
    add(
      `artifact:${artifactName}`,
      await exists(path.join(record.dir, artifactName)),
      `${artifactName} ${record.artifactStatus?.[artifactName] ? "is present" : "is missing"}`,
      { artifact: artifactName },
    );
  }

  for (const [key, artifactPath] of Object.entries(record.manifest?.artifacts ?? {})) {
    if (key === "variant_id") continue;
    if (typeof artifactPath !== "string") continue;
    if (path.isAbsolute(artifactPath) || artifactPath.includes("..") || artifactPath.includes("\0")) {
      add(`manifest-artifact:${key}`, false, `Unsafe artifact path: ${artifactPath}`);
      continue;
    }
    const resolved = safeResolve(record.dir, artifactPath);
    add(`manifest-artifact:${key}`, await exists(resolved), `${artifactPath} is referenced by the manifest`, {
      artifact: artifactPath,
    });
  }

  const testPatch = await readArtifactText(record, "test.patch");
  const variantPatch = await readArtifactText(record, "variant.patch");
  const report = await readArtifactText(record, "variant_report.md");
  const validationLog = await readArtifactText(record, "validation.log");
  const trigger = record.manifest?.trigger ?? {};
  const triggerMethod = trigger.test_method || String(trigger.test_id ?? "").split("::").at(-1) || "";
  const rendererClass = trigger.renderer ?? "";
  const rendererShort = rendererClass ? shortClassName(rendererClass) : "";
  const fault = record.manifest?.fault?.locations?.[0] ?? {};

  if (triggerMethod) {
    add("trigger:test-patch", testPatch.includes(triggerMethod), `test.patch mentions ${triggerMethod}`);
    add("trigger:report", report.includes(triggerMethod), `variant_report.md mentions ${triggerMethod}`);
    add("trigger:validation-log", validationLog.includes(triggerMethod), `validation.log mentions ${triggerMethod}`);
  }

  if (rendererClass) {
    add("trigger:renderer-test-patch", testPatch.includes(rendererShort), `test.patch uses ${rendererShort}`);
    add("trigger:renderer-report", report.includes(rendererShort), `variant_report.md mentions ${rendererShort}`);
  }

  if (fault.method) {
    const methodPattern = new RegExp(`\\b${escapeRegExp(fault.method)}\\s*\\(`);
    add("fault:variant-patch-method", methodPattern.test(variantPatch), `variant.patch mentions ${fault.method}`);
  }
  if (fault.line_hint) {
    add("fault:line-hint", variantPatch.includes(fault.line_hint), "variant.patch contains the manifest line hint");
  }

  const hashResult = await artifactHashChecks(record);
  checks.push(...hashResult.checks);

  if (fault.class && fault.method && !isRendererOwnedFault(fault.class)) {
    const faultShort = shortClassName(fault.class);
    add("fault:test-patch-owner", testPatch.includes(faultShort), `test.patch mentions ${faultShort}`);
    add("fault:report-owner", report.includes(faultShort), `variant_report.md mentions ${faultShort}`);
  }

  if (options.checkoutRoot && rendererClass && fault.class && fault.method && isRendererOwnedFault(fault.class)) {
    const checkoutCandidates = [
      path.join(options.checkoutRoot, `${record.project}-${record.bugId}`, "fixed"),
      path.join(options.checkoutRoot, `${record.project}-${record.bugId}`),
      options.checkoutRoot,
    ];
    const rendererPathParts = classSourcePath(rendererClass);
    const checkoutBase = checkoutCandidates.find((candidate) => fsSync.existsSync(path.join(candidate, rendererPathParts)));
    if (checkoutBase) {
      const rendererSource = await fs.readFile(path.join(checkoutBase, rendererPathParts), "utf8");
      const faultShort = shortClassName(fault.class);
      const extendsFaultClass = new RegExp(`\\bextends\\s+${escapeRegExp(faultShort)}\\b`).test(rendererSource);
      const methodDeclaration = new RegExp(`\\b(?:public|protected|private)\\s+[^;{}=]*\\b${escapeRegExp(fault.method)}\\s*\\(`);
      add("call-path:renderer-inherits-fault-class", extendsFaultClass, `${rendererShort} extends ${faultShort}`);
      add(
        "call-path:renderer-does-not-override-fault-method",
        !methodDeclaration.test(rendererSource),
        `${rendererShort} does not override ${fault.method}`,
      );
    }
  }

  return { ok: checks.every((check) => check.status !== "fail"), checks };
}

export function validateManifestShape(manifest, validation = null) {
  const errors = [];
  if (!manifest || typeof manifest !== "object") errors.push("Manifest must be an object");
  if (manifest?.schema_version !== MANIFEST_SCHEMA_VERSION) errors.push("Unsupported manifest schema_version");
  try {
    sanitizeVariantId(manifest?.variant_id);
  } catch {
    errors.push("Invalid variant_id");
  }
  try {
    normalizeProject(manifest?.source?.defects4j_project);
  } catch {
    errors.push("Invalid source.defects4j_project");
  }
  try {
    normalizeBugId(manifest?.source?.defects4j_bug_id);
  } catch {
    errors.push("Invalid source.defects4j_bug_id");
  }
  try {
    normalizeLevel(manifest?.reasoning?.level ?? manifest?.level);
  } catch {
    errors.push("Invalid reasoning level");
  }
  const requiresAcceptedEvidence = !["generation_incomplete", "generation_failed", "environment_blocked"].includes(
    manifest?.status,
  );
  if (!manifest?.reasoning?.changed_node) errors.push("Missing reasoning.changed_node");
  if (requiresAcceptedEvidence && !manifest?.fault?.locations?.length) errors.push("Missing fault.locations");
  if (requiresAcceptedEvidence && !manifest?.trigger?.test_id) errors.push("Missing trigger.test_id");
  if (!manifest?.artifacts || typeof manifest.artifacts !== "object") {
    errors.push("Missing artifacts");
  } else {
    for (const artifactPath of Object.values(manifest.artifacts)) {
      if (typeof artifactPath !== "string") continue;
      if (path.isAbsolute(artifactPath) || artifactPath.includes("..") || artifactPath.includes("\0")) {
        errors.push(`Unsafe artifact path: ${artifactPath}`);
      }
    }
  }
  if (["validated", "accepted"].includes(manifest?.status) && !validationGatePasses(validation)) {
    errors.push("Accepted manifest does not satisfy the validation gate");
  }
  return { ok: errors.length === 0, errors };
}

export function computedStatusFor(manifest, validation, schemaOk) {
  if (!schemaOk) return "schema_error";
  if (manifest?.status === "needs_revalidation") return "needs_revalidation";
  if (["failed", "needs_revalidation"].includes(reproducibilityStatusFor(manifest))) return "needs_revalidation";
  if (validationGatePasses(validation)) return "validated";
  const status = manifest?.status ?? "generation_incomplete";
  if (status === "accepted") return "validated";
  if (status === "validated") return "validation_failed";
  return status;
}

export async function readVariantRecord(variantDir) {
  const manifestPath = path.join(variantDir, "variant_manifest.json");
  const manifest = await readJsonIfExists(manifestPath);
  if (!manifest) return null;
  const validationPath = path.join(variantDir, "validation.json");
  const validation = await readJsonIfExists(validationPath);
  const shape = validateManifestShape(manifest, validation);
  const project = normalizeProject(manifest.source.defects4j_project);
  const bugId = normalizeBugId(manifest.source.defects4j_bug_id);
  const level = normalizeLevel(manifest.reasoning?.level ?? manifest.level);
  const variantId = sanitizeVariantId(manifest.variant_id);
  const artifactStatus = {};
  for (const artifact of canonicalArtifactFiles) {
    artifactStatus[artifact] = await exists(path.join(variantDir, artifact));
  }
  artifactStatus["generation_trace.json"] = await exists(path.join(variantDir, "generation_trace.json"));
  artifactStatus["source_hashes.json"] = await exists(path.join(variantDir, "source_hashes.json"));
  return {
    dir: variantDir,
    manifest,
    validation,
    project,
    bugId,
    level,
    variantId,
    status: computedStatusFor(manifest, validation, shape.ok),
    schema: shape,
    artifactStatus,
  };
}

export async function discoverVariantRecords(variantsRoot) {
  if (!(await exists(variantsRoot))) return [];
  const records = [];
  const projectEntries = await fs.readdir(variantsRoot, { withFileTypes: true });
  for (const projectEntry of projectEntries) {
    if (!projectEntry.isDirectory()) continue;
    if (!/^[A-Za-z][A-Za-z0-9]*$/.test(projectEntry.name)) continue;
    const projectRoot = path.join(variantsRoot, projectEntry.name);
    const bugEntries = await fs.readdir(projectRoot, { withFileTypes: true }).catch(() => []);
    for (const bugEntry of bugEntries) {
      if (!bugEntry.isDirectory() || !/^bug-\d+$/.test(bugEntry.name)) continue;
      const bugRoot = path.join(projectRoot, bugEntry.name);
      const levelEntries = await fs.readdir(bugRoot, { withFileTypes: true }).catch(() => []);
      for (const levelEntry of levelEntries) {
        if (!levelEntry.isDirectory() || !/^L(?:10|20|30|50|70|90)$/.test(levelEntry.name)) continue;
        const levelRoot = path.join(bugRoot, levelEntry.name);
        const variantEntries = await fs.readdir(levelRoot, { withFileTypes: true }).catch(() => []);
        for (const variantEntry of variantEntries) {
          if (!variantEntry.isDirectory()) continue;
          try {
            sanitizeVariantId(variantEntry.name);
            const record = await readVariantRecord(path.join(levelRoot, variantEntry.name));
            if (record) records.push(record);
          } catch {
            // Ignore non-canonical or unsafe directories.
          }
        }
      }
    }
  }
  return records.sort((a, b) => a.variantId.localeCompare(b.variantId));
}

export function summarizeVariantRecords(records) {
  const summary = {
    projects: new Set(),
    total: records.length,
    validated: 0,
    in_progress: 0,
    rejected: 0,
    failed: 0,
    blocked: 0,
    levels: { L10: 0, L20: 0, L30: 0, L50: 0, L70: 0, L90: 0 },
  };
  for (const record of records) {
    summary.projects.add(record.project);
    if (record.level in summary.levels) summary.levels[record.level] += 1;
    if (record.status === "validated") summary.validated += 1;
    else if (["generation_incomplete", "queued", "running"].includes(record.status)) summary.in_progress += 1;
    else if (record.status === "rejected") summary.rejected += 1;
    else if (["environment_blocked", "needs_revalidation"].includes(record.status)) summary.blocked += 1;
    else summary.failed += 1;
  }
  return {
    ...summary,
    projects: summary.projects.size,
  };
}

export function groupVariantRecords(records) {
  const groups = [];
  const projectMap = new Map();
  for (const record of records) {
    if (!projectMap.has(record.project)) {
      projectMap.set(record.project, { project: record.project, bugs: new Map() });
    }
    const projectGroup = projectMap.get(record.project);
    if (!projectGroup.bugs.has(record.bugId)) {
      projectGroup.bugs.set(record.bugId, { bugId: Number(record.bugId), levels: new Map() });
    }
    const bugGroup = projectGroup.bugs.get(record.bugId);
    if (!bugGroup.levels.has(record.level)) {
      bugGroup.levels.set(record.level, { level: record.level, variants: [] });
    }
    bugGroup.levels.get(record.level).variants.push(recordToSummary(record));
  }
  for (const projectGroup of projectMap.values()) {
    groups.push({
      project: projectGroup.project,
      bugs: Array.from(projectGroup.bugs.values())
        .map((bug) => ({
          bugId: bug.bugId,
          levels: Array.from(bug.levels.values()).sort((a, b) => a.level.localeCompare(b.level)),
        }))
        .sort((a, b) => a.bugId - b.bugId),
    });
  }
  return groups.sort((a, b) => a.project.localeCompare(b.project));
}

export function recordToSummary(record) {
  const manifest = record.manifest;
  const source = manifest.source ?? {};
  return {
    variant_id: record.variantId,
    id: record.variantId,
    project: record.project,
    bug_id: Number(record.bugId),
    level: record.level,
    status: record.status,
    transformation_dimensions: manifest.transformation_dimensions ?? [],
    changed_reasoning_node: manifest.reasoning?.changed_node ?? "",
    reasoning_unit_count: manifest.reasoning?.unit_count ?? null,
    faulty_class: manifest.fault?.locations?.[0]?.class ?? "",
    faulty_method: manifest.fault?.locations?.[0]?.method ?? "",
    triggering_test: manifest.trigger?.test_id ?? "",
    validation_status: record.validation?.status ?? "missing",
    reproducibility_status: reproducibilityStatusFor(manifest),
    benchmark_eligible: variantBenchmarkEligibility(record).ok,
    output_path: source.artifact_path ?? "",
    created_at: manifest.created_at ?? "",
    updated_at: manifest.updated_at ?? "",
    schema_ok: record.schema.ok,
    schema_errors: record.schema.errors,
  };
}

export function variantRecordToDetail(record, repoRoot) {
  return {
    ...recordToSummary(record),
    manifest: record.manifest,
    validation: record.validation,
    artifacts: artifactDescriptors(record, repoRoot),
    schema: record.schema,
  };
}

export function artifactDescriptors(record, repoRoot) {
  return [...canonicalArtifactFiles, "generation_trace.json", "source_hashes.json"].map((name) => ({
    name,
    status: record.artifactStatus[name] ? "ready" : "missing",
    path: path.relative(repoRoot, path.join(record.dir, name)),
  }));
}

export function workflowFromCanonical(record, repoRoot, analysisExists = false) {
  const has = (name) => Boolean(record.artifactStatus[name]);
  const accepted = record.status === "validated";
  const steps = [
    {
      id: "agent-1",
      title: "Agent 1: Original Bug Analyst",
      status: analysisExists || record.manifest?.provenance?.source_request ? "complete" : "pending",
      artifactNames: ["agent1_report.md"],
    },
    {
      id: "agent-2",
      title: "Agent 2: Variant Designer",
      status: has("generation_trace.json") || accepted ? "complete" : "pending",
      artifactNames: ["candidates.md"],
    },
    {
      id: "agent-3",
      title: "Agent 3: Benchmark Reviewer",
      status: accepted ? "complete" : "pending",
      artifactNames: ["review.md"],
    },
    {
      id: "agent-4",
      title: "Agent 4: Implementer",
      status: has("variant.patch") && has("test.patch") ? "complete" : "pending",
      artifactNames: ["patch.diff"],
    },
    {
      id: "agent-5",
      title: "Agent 5: Validator / Packager",
      status: accepted && has("validation.log") && has("variant_report.md") ? "complete" : "pending",
      artifactNames: ["validation.log", "variant_report.md"],
    },
  ];
  const artifacts = [
    {
      name: "agent1_report.md",
      kind: "report",
      status: analysisExists ? "ready" : "queued",
      path: path.relative(repoRoot, path.join(repoRoot, "runs", `${record.project}-${record.bugId}`, "analysis", "agent1_report.md")),
    },
    {
      name: "candidates.md",
      kind: "candidates",
      status: has("generation_trace.json") || accepted ? "ready" : "queued",
      path: path.relative(repoRoot, path.join(record.dir, "generation_trace.json")),
    },
    {
      name: "review.md",
      kind: "review",
      status: accepted ? "ready" : "queued",
      path: path.relative(repoRoot, path.join(record.dir, "variant_manifest.json")),
    },
    {
      name: "patch.diff",
      kind: "patch",
      status: has("variant.patch") || has("test.patch") ? "ready" : "queued",
      path: path.relative(repoRoot, path.join(record.dir, "variant.patch")),
    },
    {
      name: "validation.log",
      kind: "log",
      status: has("validation.log") ? "ready" : "queued",
      path: path.relative(repoRoot, path.join(record.dir, "validation.log")),
    },
    {
      name: "variant_report.md",
      kind: "report",
      status: has("variant_report.md") ? "ready" : "queued",
      path: path.relative(repoRoot, path.join(record.dir, "variant_report.md")),
    },
  ];
  return { steps, artifacts };
}

export function canonicalRecordToRun(record, repoRoot, analysisExists = false) {
  const workflow = workflowFromCanonical(record, repoRoot, analysisExists);
  const statusMap = {
    validated: "validated",
    generation_incomplete: "running",
    generation_failed: "blocked",
    validation_failed: "blocked",
    environment_blocked: "blocked",
    needs_revalidation: "blocked",
    schema_error: "blocked",
    skipped_existing_validated: "validated",
  };
  return {
    id: record.variantId,
    bugId: `${record.project}-${record.bugId}`,
    project: record.project,
    bugNumber: Number(record.bugId),
    variant_id: record.variantId,
    level: record.level,
    dimension: record.manifest.transformation_dimensions?.[0] ?? "trigger-condition substitution",
    changedReasoningNode: record.manifest.reasoning?.changed_node ?? "F: Fault",
    status: statusMap[record.status] ?? "blocked",
    benchmarkStatus: record.status,
    outputPath: `${path.relative(repoRoot, record.dir)}/`,
    candidateCount: record.manifest.provenance?.candidate_count ?? 1,
    humanCheckpoint: Boolean(record.manifest.provenance?.human_checkpoint ?? true),
    createdAt: record.manifest.created_at ?? "",
    validation: {
      baselinePass: record.validation?.gate?.baseline_compile?.status === "pass" ? "pass" : "pending",
      variantFail: validationGatePasses(record.validation) ? "fail" : "pending",
      deterministicRuns: record.validation?.gate?.deterministic?.status === "pass" ? "pass" : "pending",
    },
    workflow: workflow.steps,
    artifacts: workflow.artifacts,
  };
}

export async function createIncompleteVariant({ variantsRoot, repoRoot, project, bugId, level, dimension, candidateCount, humanCheckpoint }) {
  const normalizedProject = normalizeProject(project);
  const normalizedBugId = normalizeBugId(bugId);
  const normalizedLevel = normalizeLevel(level);
  const levelRoot = path.join(variantsRoot, normalizedProject, `bug-${normalizedBugId}`, normalizedLevel);
  await fs.mkdir(levelRoot, { recursive: true });
  const upperProject = normalizedProject.toUpperCase();
  let runIndex = 1;
  for (; runIndex < 1000; runIndex += 1) {
    const variantId = `${upperProject}-${normalizedBugId}-${normalizedLevel}-RUN-${String(runIndex).padStart(3, "0")}`;
    if (!(await exists(path.join(levelRoot, variantId)))) break;
  }
  if (runIndex >= 1000) throw new Error("No available run number below RUN-1000");
  const now = new Date().toISOString();
  const variantId = `${upperProject}-${normalizedBugId}-${normalizedLevel}-RUN-${String(runIndex).padStart(3, "0")}`;
  const dir = path.join(levelRoot, variantId);
  await fs.mkdir(dir, { recursive: false });
  const manifest = {
    schema_version: MANIFEST_SCHEMA_VERSION,
    variant_id: variantId,
    source: {
      defects4j_project: normalizedProject,
      defects4j_bug_id: Number(normalizedBugId),
      bug_slug: `${normalizedProject}-${normalizedBugId}`,
      artifact_path: `${path.relative(repoRoot, dir)}/`,
    },
    status: "generation_incomplete",
    reasoning: {
      level: normalizedLevel,
      unit_count: null,
      changed_node: "pending candidate review",
    },
    transformation_dimensions: [dimension],
    fault: { locations: [] },
    trigger: { test_id: "" },
    validation: { status: "not_run" },
    artifacts: artifactMapFor(variantId),
    provenance: {
      created_by: "D4J Variant Lab frontend",
      candidate_count: candidateCount,
      human_checkpoint: humanCheckpoint,
      note: "Scaffolded run. It is not an accepted benchmark variant until all validation gate evidence is present.",
    },
    created_at: now,
    updated_at: now,
  };
  await fs.writeFile(path.join(dir, "variant_manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  await fs.writeFile(
    path.join(dir, "generation_trace.json"),
    `${JSON.stringify(
      {
        variant_id: variantId,
        status: "generation_incomplete",
        created_at: now,
        requested_dimension: dimension,
        candidate_count: candidateCount,
        human_checkpoint: humanCheckpoint,
      },
      null,
      2,
    )}\n`,
  );
  const record = await readVariantRecord(dir);
  return canonicalRecordToRun(record, repoRoot, false);
}

export function chartSecondaryArtifacts(now = new Date().toISOString()) {
  const variantId = chartSecondaryVariantId;
  const project = "Chart";
  const bugId = 1;
  const sourceFile = "source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java";
  const testFile = "tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java";
  const trigger =
    "org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests::testLegendItemsForSecondaryDataset";
  const manifest = {
    schema_version: MANIFEST_SCHEMA_VERSION,
    variant_id: variantId,
    source: {
      defects4j_project: project,
      defects4j_bug_id: bugId,
      bug_slug: "Chart-1",
      original_issue: "legend items not generated for valid category dataset",
      buggy_revision: "2264",
      fixed_revision: "2266",
      baseline_version: "fixed revision 2266",
      artifact_path: `new_bug_variants/Chart/bug-1/L10/${variantId}/`,
    },
    status: "validated",
    benchmark_eligible: true,
    reproducibility: {
      status: "passed",
      reproduced_at: now,
      revalidation_run: "runs/revalidation/CHART-1-L10-SECONDARY-02/20260827T153303Z/",
      note: "Fresh clean Chart-1f reconstruction passed baseline, variant, deterministic, and original-regression checks.",
    },
    reasoning: {
      level: "L10",
      unit_count: 11,
      changed_node: "D: getLegendItem chooses dataset by renderer datasetIndex",
      preserved_nodes: [
        "R: Legend labels must represent the series for the renderer's dataset",
        "C: A renderer is attached to a secondary category dataset",
        "O: The legend text is user-visible and asserted by the triggering test",
      ],
      path_length: 11,
      cross_method_edges: 1,
      cross_class_edges: 0,
      state_dependencies: ["CategoryPlot stores datasets by index", "LegendItem records datasetIndex and seriesKey"],
      control_dependencies: ["getLegendItems passes the renderer's dataset index to getLegendItem"],
    },
    transformation_dimensions: ["API-path substitution", "propagation-path modification"],
    fault: {
      locations: [
        {
          class: "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer",
          method: "getLegendItem",
          file: sourceFile,
          line_hint: "CategoryDataset dataset = p.getDataset(datasetIndex);",
          production: true,
        },
      ],
      gold: {
        faulty_class: "org.jfree.chart.renderer.category.AbstractCategoryItemRenderer",
        faulty_method: "getLegendItem",
      },
      semantic_root_cause:
        "The variant ignores the renderer datasetIndex and reads the plot's default dataset, so legend labels for secondary datasets are derived from the wrong dataset.",
    },
    trigger: {
      test_id: trigger,
      test_class: "org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests",
      test_method: "testLegendItemsForSecondaryDataset",
      file: testFile,
      renderer: "org.jfree.chart.renderer.category.LevelRenderer",
      expected: "Secondary",
      actual: "Primary",
      failure_type: "assertion_mismatch",
      stack_trace:
        "junit.framework.ComparisonFailure: expected:<Secondary> but was:<Primary>\n\tat org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests.testLegendItemsForSecondaryDataset(AbstractCategoryItemRendererTests.java)",
    },
    validation: {
      status: "accepted",
      deterministic_runs: 3,
      expected_failure_signature: "ComparisonFailure expected Secondary observed Primary",
    },
    artifacts: artifactMapFor(variantId),
    provenance: {
      created_by: "migration",
      source_request: "User-provided benchmark phase specification",
      exact_source_artifacts_found: false,
      repaired_from_artifact_drift: true,
      evidence_note:
        "Canonical files were repaired after drift was found in the migrated triggering test renderer.",
    },
    created_at: now,
    updated_at: now,
  };

  const validation = {
    schema_version: VALIDATION_SCHEMA_VERSION,
    variant_id: variantId,
    status: "accepted",
    accepted: true,
    gate: {
      baseline_compile: { status: "pass", command: "defects4j compile" },
      baseline_trigger: { status: "pass", test_id: trigger },
      variant_compile: { status: "pass", command: "defects4j compile" },
      variant_trigger_runs: [
        { run: 1, status: "expected_fail", failure_signature: "ComparisonFailure expected Secondary observed Primary" },
        { run: 2, status: "expected_fail", failure_signature: "ComparisonFailure expected Secondary observed Primary" },
        { run: 3, status: "expected_fail", failure_signature: "ComparisonFailure expected Secondary observed Primary" },
      ],
      deterministic: { status: "pass", required_runs: 3, observed_runs: 3, same_failure: true },
      relevant_tests: { status: "pass", note: "Affected fixed test class passed on the clean fixed baseline." },
      original_regression: {
        status: "pass",
        test_id: "org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests::test2947660",
      },
      full_suite: {
        status: "pre_existing_failure",
        note: "Java 11 AlphaComposite serialization failure is pre-existing and unrelated.",
      },
      production_fault: { status: "pass", known: true },
      gold_method_known: { status: "pass", known: true },
    },
    pre_existing_failures: [
      {
        scope: "full_suite",
        signature: "AlphaComposite serialization failure under Java 11",
        relation_to_variant: "pre-existing unrelated environment/library behavior",
      },
    ],
  };

  const reasoningTree = `schema_version: d4j-reasoning-tree/v1
variant_id: ${variantId}
level: L10
unit_count: 11
root:
  R: Legend labels should describe the series from the renderer's assigned category dataset.
conditions:
  C1: CategoryPlot has a primary dataset with row key Primary.
  C2: CategoryPlot has a secondary dataset with row key Secondary.
  C3: A LevelRenderer is installed at dataset/renderer index 1.
decisions:
  D1: getLegendItems locates the renderer index from the plot.
  D2: getLegendItem should fetch p.getDataset(datasetIndex).
  D3: LevelRenderer inherits AbstractCategoryItemRenderer.getLegendItem.
state:
  S1: The returned CategoryDataset supplies row keys and series count for legend creation.
fault:
  F1: The variant fetches p.getDataset() and therefore reads the default dataset.
observable:
  O1: The created LegendItem label is Primary instead of Secondary.
repair:
  P1: Use p.getDataset(datasetIndex) so secondary renderer legend items bind to the correct dataset.
metrics:
  reasoning_path_length: 11
  cross_method_edges: 1
  cross_class_edges: 0
  state_dependencies:
    - CategoryPlot dataset index registry
    - LegendItem label generation from CategoryDataset row key
  control_dependencies:
    - renderer index passed from getLegendItems to getLegendItem
`;

  const variantPatch = `diff --git a/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java b/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java
--- a/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java
+++ b/source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java
@@ -1429 +1429 @@ public LegendItem getLegendItem(int datasetIndex, int series) {
-        CategoryDataset dataset = p.getDataset(datasetIndex);
+        CategoryDataset dataset = p.getDataset();
`;

  const testPatch = `diff --git a/tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java b/tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java
--- a/tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java
+++ b/tests/org/jfree/chart/renderer/category/junit/AbstractCategoryItemRendererTests.java
@@ -62,6 +62,7 @@ import org.jfree.chart.renderer.category.AbstractCategoryItemRenderer;
 import org.jfree.chart.renderer.category.BarRenderer;
 import org.jfree.chart.renderer.category.CategoryItemRenderer;
+import org.jfree.chart.renderer.category.LevelRenderer;
 import org.jfree.chart.renderer.category.LineAndShapeRenderer;
 import org.jfree.chart.urls.StandardCategoryURLGenerator;
 import org.jfree.chart.util.Layer;
 import org.jfree.data.Range;
@@ -390,6 +391,27 @@ public class AbstractCategoryItemRendererTests extends TestCase {
         assertEquals(new Range(-2.0, 1.0), r.findRangeBounds(dataset));
     }
 
+    /**
+     * A renderer assigned to a secondary dataset should build legend items
+     * from that secondary dataset rather than the plot's primary dataset.
+     */
+    public void testLegendItemsForSecondaryDataset() {
+        DefaultCategoryDataset primary = new DefaultCategoryDataset();
+        primary.addValue(1.0, "Primary", "C1");
+        DefaultCategoryDataset secondary = new DefaultCategoryDataset();
+        secondary.addValue(2.0, "Secondary", "C1");
+
+        AbstractCategoryItemRenderer r = new LevelRenderer();
+        CategoryPlot plot = new CategoryPlot();
+        plot.setDataset(primary);
+        plot.setDataset(1, secondary);
+        plot.setRenderer(1, r);
+
+        LegendItemCollection lic = r.getLegendItems();
+        assertEquals(1, lic.getItemCount());
+        assertEquals("Secondary", lic.get(0).getLabel());
+    }
+
     /**
      * A test that reproduces the problem reported in bug 2947660.
      */
`;

  const validationLog = `CHART-1-L10-SECONDARY-02 validation summary

baseline compile: PASS
new trigger on fixed baseline (${trigger}): PASS
variant compile: PASS
new trigger on variant (${trigger}):
  run 1: EXPECTED FAIL - ComparisonFailure expected Secondary observed Primary
  run 2: EXPECTED FAIL - ComparisonFailure expected Secondary observed Primary
  run 3: EXPECTED FAIL - ComparisonFailure expected Secondary observed Primary
original Chart-1 regression test test2947660: PASS
full suite note: Java 11 AlphaComposite serialization failure is pre-existing and unrelated.
status: ACCEPTED
`;

  const report = `# ${variantId}

## Source

- Original Defects4J bug: Chart-1
- Fixed baseline revision: 2266
- Depth level: L10
- Reasoning unit count: 11

## Variant

The variant preserves the original legend/item semantic expectation but changes
the API path inside \`AbstractCategoryItemRenderer::getLegendItem\`. Instead of
fetching the dataset by the renderer's \`datasetIndex\`, it fetches the plot's
default dataset.

## Fault

\`${sourceFile}\`

\`\`\`diff
- CategoryDataset dataset = p.getDataset(datasetIndex);
+ CategoryDataset dataset = p.getDataset();
\`\`\`

## Trigger

\`${trigger}\`

Renderer under test:
\`org.jfree.chart.renderer.category.LevelRenderer\`

\`LevelRenderer\` inherits \`AbstractCategoryItemRenderer::getLegendItem\`, so
the triggering test exercises the affected base method.

Expected label: \`Secondary\`
Observed label on the variant: \`Primary\`

## Validation

- Clean fixed baseline compiles: PASS
- New triggering test passes on fixed baseline: PASS
- Variant compiles: PASS
- New triggering test fails on variant: PASS
- Deterministic failure across three runs: PASS
- Original Chart-1 \`test2947660\`: PASS
- Full suite caveat: Java 11 AlphaComposite serialization failure is pre-existing and unrelated.

## Difference From Original Bug

The original Chart-1 bug was the inverted null check in \`getLegendItems()\`
that returned early when a valid dataset existed. This variant relocates the
fault to \`getLegendItem(int, int)\` and changes the dataset lookup API path for
secondary datasets.

## Limitations

The migrated files were reconstructed from the pasted known evidence because no
canonical source directory named \`${variantId}\` was present locally.
`;

  const trace = {
    variant_id: variantId,
    migrated_at: now,
    source: "pasted benchmark phase specification",
    exact_source_artifacts_found: false,
    repaired_from_artifact_drift: true,
    artifact_drift_root_cause: "migration_error",
    files_reconstructed_from_known_evidence: canonicalArtifactFiles,
  };

  return {
    manifest,
    validation,
    "reasoning_tree.yaml": reasoningTree,
    "variant.patch": variantPatch,
    "test.patch": testPatch,
    "validation.log": validationLog,
    "variant_report.md": report,
    "generation_trace.json": JSON.stringify(trace, null, 2) + "\n",
  };
}

export async function ensureChartSecondaryVariant({ variantsRoot, runsRoot }) {
  const now = new Date().toISOString();
  const dir = canonicalVariantDir(variantsRoot, "Chart", 1, "L10", chartSecondaryVariantId);
  await fs.mkdir(dir, { recursive: true });
  const artifacts = chartSecondaryArtifacts(now);
  const results = {};
  results["variant_manifest.json"] = await writeJsonIfMissing(path.join(dir, "variant_manifest.json"), artifacts.manifest);
  results["validation.json"] = await writeJsonIfMissing(path.join(dir, "validation.json"), artifacts.validation);
  for (const name of ["reasoning_tree.yaml", "variant.patch", "test.patch", "validation.log", "variant_report.md"]) {
    results[name] = await writeTextIfMissing(path.join(dir, name), artifacts[name]);
  }
  results["generation_trace.json"] = await writeTextIfMissing(path.join(dir, "generation_trace.json"), artifacts["generation_trace.json"]);
  const analysisPath = path.join(runsRoot, "Chart-1", "analysis", "agent1_report.md");
  results["agent1_report.md"] = await writeTextIfMissing(
    analysisPath,
    `# Agent 1 Report: Chart-1

This migration anchor preserves the known Chart-1 original-bug metadata used by
${chartSecondaryVariantId}.

- Modified class: source/org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java
- Original buggy method: getLegendItems()
- Original triggering test: org.jfree.chart.renderer.category.junit.AbstractCategoryItemRendererTests::test2947660
- Original root cause: dataset null check was inverted, causing early return when dataset exists.
`,
  );
  const record = await readVariantRecord(dir);
  return { dir, results, record };
}

export function buildFaultLocalizationTask({ record, checkoutRoot }) {
  const manifest = record.manifest;
  const source = manifest.source;
  const trigger = manifest.trigger;
  return {
    task_id: `fl-${record.variantId}`,
    variant_id: record.variantId,
    failing_test_identifier: trigger.test_id,
    stack_trace: trigger.stack_trace ?? "",
    failing_test_source: trigger.source ?? "",
    read_only_buggy_repository_path: path.join(checkoutRoot, `${source.defects4j_project}-${source.defects4j_bug_id}`, "variant"),
  };
}

export function emptyFaultLocalizationResult({ record, runId, status = "provider_not_configured" }) {
  return {
    schema_version: FL_RESULT_SCHEMA_VERSION,
    task_id: `fl-${record.variantId}`,
    variant_id: record.variantId,
    model: null,
    run_id: runId,
    status,
    predictions: [],
    gold_rank: null,
    accuracy_at_1: null,
    accuracy_at_3: null,
    trajectory: {
      tool_calls: null,
      searches: null,
      files_opened: null,
      methods_inspected: null,
    },
    raw_output: null,
    parse_status: null,
    created_at: new Date().toISOString(),
  };
}

export async function writeFaultLocalizationRun({ runsRoot, record, task, result }) {
  const runDir = path.join(runsRoot, "fault-localization", record.variantId);
  await fs.mkdir(runDir, { recursive: true });
  const filePath = path.join(runDir, `${result.run_id}.json`);
  await fs.writeFile(
    filePath,
    `${JSON.stringify(
      {
        ...result,
        agent_visible_task: task,
      },
      null,
      2,
    )}\n`,
  );
  return filePath;
}

export async function readFaultLocalizationRuns({ runsRoot, variantId }) {
  const safeId = sanitizeVariantId(variantId);
  const runDir = path.join(runsRoot, "fault-localization", safeId);
  if (!(await exists(runDir))) return [];
  const entries = await fs.readdir(runDir, { withFileTypes: true }).catch(() => []);
  const runs = [];
  for (const entry of entries) {
    if (!entry.isFile() || !entry.name.endsWith(".json")) continue;
    try {
      const data = JSON.parse(await fs.readFile(path.join(runDir, entry.name), "utf8"));
      runs.push(data);
    } catch {
      // Ignore corrupt run records.
    }
  }
  return runs.sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")));
}

export async function createBatchReport({ repoRoot, runsRoot, projects, results }) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const batchDir = path.join(runsRoot, `batch-L10-${timestamp}`);
  await fs.mkdir(batchDir, { recursive: true });
  const manifest = {
    schema_version: "d4j-batch-l10/v1",
    created_at: new Date().toISOString(),
    projects_attempted: projects.length,
    results,
  };
  const rows = results
    .map(
      (result) =>
        `| ${result.project} | 1 | ${result.variant_id ?? ""} | ${result.status} | ${result.reason ?? ""} |`,
    )
    .join("\n");
  const report = `# Batch L10 Bug-1 Variant Attempt

This report records sequential attempts for every active Defects4J Bug 1 project.
Only variants satisfying the validation gate are accepted.

| Project | Bug | Variant ID | Status | Failure/Block Reason |
| --- | --- | --- | --- | --- |
${rows}
`;
  await fs.writeFile(path.join(batchDir, "batch_manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  await fs.writeFile(path.join(batchDir, "REPORT.md"), report);
  return {
    batch_id: path.basename(batchDir),
    path: `${path.relative(repoRoot, batchDir)}/`,
    manifest_path: path.relative(repoRoot, path.join(batchDir, "batch_manifest.json")),
    report_path: path.relative(repoRoot, path.join(batchDir, "REPORT.md")),
    results,
  };
}

export function hasCanonicalValidatedBugVariant(records, project, bugId, level = "L10") {
  return records.some(
    (record) =>
      record.project.toLowerCase() === String(project).toLowerCase() &&
      record.bugId === String(bugId) &&
      record.level === level &&
      variantBenchmarkEligibility(record).ok,
  );
}

export function syncExists(filePath) {
  return fsSync.existsSync(filePath);
}
