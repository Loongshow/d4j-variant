/**
 * Semantic-depth auditing (issues F-5 and F-10).
 *
 * The benchmark's independent variable is "minimum verified semantic dependency":
 * the number of irreducible, evidence-backed inference units in the SHORTEST valid
 * localization proof. A manifest's declared `reasoning.unit_count` is a NOMINAL label
 * asserted at construction time. It is not the same quantity, and several historical
 * manifests carry round nominal values (50, 50, 50, 70) that the project's own human
 * shortest-path audits do not support.
 *
 * This module separates the two quantities and refuses to conflate them:
 *
 *   nominal_depth            - the level label the artifact was packaged under
 *   audited_semantic_depth   - the count an explicit audit defends
 *   depth_audit_status       - how, and whether, that audit was performed
 *   depth_audit_report       - where the reasoning is written down
 *
 * It performs the MECHANICAL half of an audit (structure of the declared dependency
 * graph) and records, but never invents, the HUMAN half (shortest-path pruning).
 */

import fs from "node:fs/promises";

export const SEMANTIC_DEPTH_SCHEMA_VERSION = "d4j-semantic-depth-audit/v1";
export const DEPTH_AUDIT_REGISTRY_SCHEMA_VERSION = "d4j-depth-audit-registry/v1";

/** Strict lower bounds. These are thresholds, not equalities. */
export const STRICT_DEPTH_THRESHOLDS = Object.freeze({
  L10: 10,
  L20: 20,
  L30: 30,
  L50: 50,
  L70: 70,
  L90: 90,
});

export const DEPTH_AUDIT_STATUS = Object.freeze({
  STRICT_PASS: "audited_strict_pass",
  STRICT_FAIL: "audited_strict_fail",
  NOMINAL_ONLY: "nominal_only",
  NOT_AUDITED: "not_audited",
});

export const DEPTH_AUDIT_METHOD = Object.freeze({
  STRUCTURAL: "structural_dag_verification",
  HUMAN_SHORTEST_PATH: "human_shortest_path_audit",
  BOTH: "structural_and_human",
  NONE: "not_audited",
});

export const REASONING_TREE_FORMAT = Object.freeze({
  UNIT_DAG: "semantic_units_dag",
  JSON_LINEAR_PATH: "json_linear_path",
  CATEGORIZED_YAML: "categorized_yaml",
  UNKNOWN: "unknown",
});

/* ------------------------------------------------------------------- parsing */

function stripQuotes(value) {
  const text = String(value ?? "").trim();
  if ((text.startsWith('"') && text.endsWith('"')) || (text.startsWith("'") && text.endsWith("'"))) {
    return text.slice(1, -1);
  }
  return text;
}

function parseInlineList(value) {
  const text = String(value ?? "").trim();
  if (!text.startsWith("[")) return [];
  return text
    .slice(1, text.endsWith("]") ? -1 : undefined)
    .split(",")
    .map((item) => stripQuotes(item))
    .filter(Boolean);
}

/**
 * Splits a YAML flow mapping body on top-level commas only, so that a quoted
 * inference containing a comma is not shredded.
 */
function splitFlowEntries(body) {
  const entries = [];
  let depth = 0;
  let quote = null;
  let current = "";
  for (const char of body) {
    if (quote) {
      current += char;
      if (char === quote) quote = null;
      continue;
    }
    if (char === '"' || char === "'") {
      quote = char;
      current += char;
      continue;
    }
    if (char === "[" || char === "{") depth += 1;
    if (char === "]" || char === "}") depth -= 1;
    if (char === "," && depth === 0) {
      entries.push(current);
      current = "";
      continue;
    }
    current += char;
  }
  if (current.trim()) entries.push(current);
  return entries;
}

function parseFlowUnit(body) {
  const unit = { id: "", inference: "", depends_on: [], evidence: [], role: "" };
  for (const entry of splitFlowEntries(body)) {
    const separator = entry.indexOf(":");
    if (separator === -1) continue;
    const key = entry.slice(0, separator).trim();
    const rawValue = entry.slice(separator + 1).trim();
    if (key === "depends_on" || key === "evidence") unit[key] = parseInlineList(rawValue);
    else if (key in unit) unit[key] = stripQuotes(rawValue);
  }
  return unit;
}

/**
 * Deliberately minimal reader for the two shapes this repository actually uses.
 * It never guesses: an unrecognised document yields format "unknown" and zero units,
 * which downstream reports as "not audited" rather than as a depth of zero.
 */
export function parseReasoningTreeDocument(text) {
  const raw = String(text ?? "");
  const result = {
    format: REASONING_TREE_FORMAT.UNKNOWN,
    declared_level: null,
    declared_unit_count: null,
    dependency_edges_declared: false,
    units: [],
  };
  if (!raw.trim()) return result;

  // Closure-era trees are JSON documents stored under a .yaml name.
  if (raw.trimStart().startsWith("{")) {
    let parsed = null;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return result;
    }
    const path = Array.isArray(parsed?.shortest_reasoning_path) ? parsed.shortest_reasoning_path : [];
    result.format = path.length ? REASONING_TREE_FORMAT.JSON_LINEAR_PATH : REASONING_TREE_FORMAT.UNKNOWN;
    result.declared_level = parsed?.reasoning_level ?? null;
    result.declared_unit_count =
      Number.isFinite(parsed?.semantic_inference_steps) ? parsed.semantic_inference_steps : null;
    result.units = path.map((inference, index) => ({
      id: `P${String(index + 1).padStart(2, "0")}`,
      inference: String(inference ?? ""),
      depends_on: [],
      evidence: [],
      role: "",
    }));
    return result;
  }

  const lines = raw.split("\n");
  const topLevel = {};
  for (const line of lines) {
    const match = /^([A-Za-z_][\w]*):\s*(.*)$/.exec(line);
    if (match) topLevel[match[1]] = match[2].trim();
  }
  result.declared_level = topLevel.level ? stripQuotes(topLevel.level) : null;
  result.declared_unit_count = Number.isFinite(Number(topLevel.unit_count)) && topLevel.unit_count !== ""
    ? Number(topLevel.unit_count)
    : null;

  const unitsIndex = lines.findIndex((line) => /^semantic_units:\s*$/.test(line));
  if (unitsIndex !== -1) {
    result.format = REASONING_TREE_FORMAT.UNIT_DAG;
    let current = null;
    for (const line of lines.slice(unitsIndex + 1)) {
      if (/^\S/.test(line) && line.trim()) break;
      const flow = /^\s*-\s*\{(.*)\}\s*,?\s*$/.exec(line);
      if (flow) {
        current = parseFlowUnit(flow[1]);
        result.units.push(current);
        continue;
      }
      const blockStart = /^\s*-\s+id:\s*(.+)$/.exec(line);
      if (blockStart) {
        current = { id: stripQuotes(blockStart[1]), inference: "", depends_on: [], evidence: [], role: "" };
        result.units.push(current);
        continue;
      }
      const field = /^\s+([A-Za-z_][\w]*):\s*(.*)$/.exec(line);
      if (field && current) {
        const [, key, value] = field;
        if (key === "depends_on" || key === "evidence") current[key] = parseInlineList(value);
        else if (key in current) current[key] = stripQuotes(value);
      }
    }
    result.dependency_edges_declared = result.units.some((unit) => unit.depends_on.length > 0);
    return result;
  }

  // Chart-era trees: category maps (root / conditions / decisions / state / fault / ...)
  const categories = ["root", "conditions", "decisions", "state", "fault", "observable", "repair", "propagation"];
  let activeCategory = null;
  for (const line of lines) {
    const categoryMatch = /^([A-Za-z_][\w]*):\s*$/.exec(line);
    if (categoryMatch) {
      activeCategory = categories.includes(categoryMatch[1]) ? categoryMatch[1] : null;
      continue;
    }
    const entry = /^\s{2,}([A-Za-z]+\d*):\s*(.+)$/.exec(line);
    if (entry && activeCategory) {
      result.units.push({
        id: entry[1],
        inference: stripQuotes(entry[2]),
        depends_on: [],
        evidence: [],
        role: activeCategory,
      });
    }
  }
  if (result.units.length) result.format = REASONING_TREE_FORMAT.CATEGORIZED_YAML;
  return result;
}

/* ------------------------------------------------------------------ auditing */

function longestPathLength(nodeIds, parentsById) {
  const memo = new Map();
  const visiting = new Set();
  let cyclic = false;
  const depthOf = (id) => {
    if (memo.has(id)) return memo.get(id);
    if (visiting.has(id)) {
      cyclic = true;
      return 0;
    }
    visiting.add(id);
    const parents = parentsById.get(id) ?? [];
    const value = parents.length === 0 ? 1 : 1 + Math.max(...parents.map((parent) => depthOf(parent)));
    visiting.delete(id);
    memo.set(id, value);
    return value;
  };
  let longest = 0;
  for (const id of nodeIds) longest = Math.max(longest, depthOf(id));
  return { longest, cyclic };
}

/**
 * MECHANICAL half of a depth audit. Reports what the declared dependency graph
 * actually is. It never claims to measure irreducibility - that requires the human
 * shortest-path procedure recorded in semantic-unit-annotation-protocol.md.
 */
export function auditReasoningTree(document) {
  const units = document?.units ?? [];
  const ids = units.map((unit) => unit.id);
  const idSet = new Set(ids);
  const duplicateIds = ids.filter((id, index) => ids.indexOf(id) !== index);

  const normalized = units.map((unit) => unit.inference.trim().toLowerCase().replace(/\s+/g, " "));
  const duplicateInferences = normalized.filter(
    (value, index) => value && normalized.indexOf(value) !== index,
  );

  const parentsById = new Map();
  const childCount = new Map();
  const missingDependencies = [];
  for (const unit of units) {
    const parents = (unit.depends_on ?? []).filter(Boolean);
    for (const parent of parents) {
      if (!idSet.has(parent)) missingDependencies.push({ unit: unit.id, missing: parent });
      childCount.set(parent, (childCount.get(parent) ?? 0) + 1);
    }
    parentsById.set(unit.id, parents.filter((parent) => idSet.has(parent)));
  }

  const structural = document?.dependency_edges_declared === true;
  const { longest, cyclic } = structural ? longestPathLength(ids, parentsById) : { longest: null, cyclic: false };
  const joins = structural ? units.filter((unit) => (unit.depends_on ?? []).length >= 2).length : null;
  const peakBranching = structural ? Math.max(0, ...[...childCount.values()]) : null;
  const roots = structural ? units.filter((unit) => (unit.depends_on ?? []).length === 0).map((unit) => unit.id) : [];
  const leaves = structural ? ids.filter((id) => !childCount.has(id)) : [];
  const linear =
    structural &&
    units.every((unit) => (unit.depends_on ?? []).length <= 1) &&
    [...childCount.values()].every((count) => count <= 1);

  return {
    schema_version: SEMANTIC_DEPTH_SCHEMA_VERSION,
    format: document?.format ?? REASONING_TREE_FORMAT.UNKNOWN,
    declared_level: document?.declared_level ?? null,
    declared_unit_count: document?.declared_unit_count ?? null,
    parsed_unit_count: units.length,
    unit_count_agrees_with_declaration:
      document?.declared_unit_count == null ? null : document.declared_unit_count === units.length,
    dependency_edges_declared: structural,
    duplicate_unit_ids: [...new Set(duplicateIds)],
    duplicate_inferences: [...new Set(duplicateInferences)],
    missing_dependencies: missingDependencies,
    has_cycle: cyclic,
    // Named distinctly from the manifests' own `dependency_depth` / `evidence_joins`
    // fields, which were authored under the constructor's definitions. These two are
    // mechanical graph measurements and are not assertions that a manifest is wrong.
    longest_dependency_chain_nodes: longest,
    multi_parent_nodes: joins,
    peak_branching_factor: peakBranching,
    root_count: structural ? roots.length : null,
    leaf_count: structural ? leaves.length : null,
    structure_class: structural ? (linear ? "linear_chain" : "branched_dag") : "not_declared",
    structurally_auditable: structural && !cyclic && missingDependencies.length === 0,
  };
}

export function strictThresholdFor(level) {
  return STRICT_DEPTH_THRESHOLDS[String(level ?? "").toUpperCase()] ?? null;
}

/**
 * A level label is a LOWER BOUND, never an equality requirement.
 */
export function strictDepthVerdict({ level, auditedSemanticDepth }) {
  const threshold = strictThresholdFor(level);
  if (threshold == null) {
    return { ok: false, threshold: null, reason: `Unknown depth level ${level}` };
  }
  if (!Number.isFinite(auditedSemanticDepth)) {
    return { ok: false, threshold, reason: `No audited semantic depth is recorded for ${level}` };
  }
  if (auditedSemanticDepth < threshold) {
    return {
      ok: false,
      threshold,
      reason: `Audited semantic depth ${auditedSemanticDepth} is below the strict ${level} lower bound of ${threshold}`,
    };
  }
  return { ok: true, threshold, reason: `Audited semantic depth ${auditedSemanticDepth} meets the strict ${level} lower bound of ${threshold}` };
}

/* ------------------------------------------------------------------ registry */

export function emptyDepthAuditRegistry() {
  return {
    schema_version: DEPTH_AUDIT_REGISTRY_SCHEMA_VERSION,
    entries: {},
  };
}

export async function loadDepthAuditRegistry(registryPath) {
  try {
    const parsed = JSON.parse(await fs.readFile(registryPath, "utf8"));
    if (parsed?.schema_version !== DEPTH_AUDIT_REGISTRY_SCHEMA_VERSION) return emptyDepthAuditRegistry();
    return { ...emptyDepthAuditRegistry(), ...parsed, entries: parsed.entries ?? {} };
  } catch {
    return emptyDepthAuditRegistry();
  }
}

/**
 * Resolves the depth facts for one variant WITHOUT mutating its historical manifest.
 * The registry is additive and external precisely so that historical artifacts stay
 * byte-identical.
 */
export function resolveDepthAudit(variantId, registry, manifest = null) {
  const nominalDepth = manifest?.reasoning?.level ?? manifest?.depth ?? manifest?.level ?? null;
  const nominalUnitCount = manifest?.reasoning?.unit_count ?? null;
  const entry = registry?.entries?.[variantId] ?? null;
  if (!entry) {
    return {
      variant_id: variantId,
      nominal_depth: nominalDepth,
      nominal_unit_count: nominalUnitCount,
      audited_semantic_depth: null,
      depth_audit_status: DEPTH_AUDIT_STATUS.NOT_AUDITED,
      depth_audit_method: DEPTH_AUDIT_METHOD.NONE,
      depth_audit_report: null,
      strict_depth_ok: false,
      strict_reason: "No depth audit is recorded for this variant",
    };
  }
  const audited = Number.isFinite(entry.audited_semantic_depth) ? entry.audited_semantic_depth : null;
  const verdict = strictDepthVerdict({ level: entry.nominal_depth ?? nominalDepth, auditedSemanticDepth: audited });
  const status =
    entry.depth_audit_status ??
    (audited == null
      ? DEPTH_AUDIT_STATUS.NOT_AUDITED
      : verdict.ok
        ? DEPTH_AUDIT_STATUS.STRICT_PASS
        : DEPTH_AUDIT_STATUS.STRICT_FAIL);
  return {
    variant_id: variantId,
    nominal_depth: entry.nominal_depth ?? nominalDepth,
    nominal_unit_count: entry.nominal_unit_count ?? nominalUnitCount,
    audited_semantic_depth: audited,
    depth_audit_status: status,
    depth_audit_method: entry.depth_audit_method ?? DEPTH_AUDIT_METHOD.NONE,
    depth_audit_report: entry.depth_audit_report ?? null,
    annotation_status: entry.annotation_status ?? "single_rater",
    strict_depth_ok: status === DEPTH_AUDIT_STATUS.STRICT_PASS && verdict.ok,
    strict_reason: verdict.reason,
    notes: entry.notes ?? null,
  };
}

/**
 * Strict-cohort gate. `nominal L50 + audited 38` must NOT be usable as an L50
 * condition, however useful it remains as a historical artifact.
 */
export function strictDepthEligibility(variantId, registry, manifest = null) {
  const resolved = resolveDepthAudit(variantId, registry, manifest);
  const reasons = [];
  if (resolved.depth_audit_status === DEPTH_AUDIT_STATUS.NOT_AUDITED) {
    reasons.push(`${variantId} has no recorded depth audit`);
  }
  if (resolved.depth_audit_status === DEPTH_AUDIT_STATUS.NOMINAL_ONLY) {
    reasons.push(`${variantId} is nominal_only: its declared level is not supported by an audit`);
  }
  if (resolved.depth_audit_status === DEPTH_AUDIT_STATUS.STRICT_FAIL) {
    reasons.push(`${variantId}: ${resolved.strict_reason}`);
  }
  return { ok: reasons.length === 0, reasons, resolved };
}
