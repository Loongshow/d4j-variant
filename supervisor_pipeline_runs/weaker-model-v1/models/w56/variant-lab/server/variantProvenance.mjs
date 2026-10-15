/**
 * Provenance schema for STRICT variant packages (issue F-6).
 *
 * The three strict artifacts are "validated" by the code's gate, but the evidence behind
 * that word is thinner than for the packages they are compared against:
 *
 *   - validation.log: 30-40 lines of hand-written narrative vs 346-470 lines of raw
 *     captured tool output for the comparable Closure packages;
 *   - source_hashes.json: 2 touched files vs 916 files plus an aggregate digest;
 *   - reproducibility timestamps: the rounded literal 2026-09-12T12:00:00Z for all three;
 *   - no transformation_dimensions / research_metadata / contamination_metadata /
 *     provenance blocks, which the older packages carry.
 *
 * This module defines what a strict package MUST record, and validates existing packages
 * against it WITHOUT modifying them. Missing fields are reported as gaps. Nothing here
 * invents a value: a field that was never recorded stays missing.
 */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

export const VARIANT_PROVENANCE_SCHEMA_VERSION = "d4j-variant-provenance/v1";
export const PROVENANCE_SUPPLEMENT_SCHEMA_VERSION = "d4j-provenance-supplement/v1";

/**
 * Fields that a NEW strict package must record inside the package itself. A supplement
 * may not stand in for these: if a package is built today, its own validation record is
 * expected to name the validator that produced it.
 */
export const IN_PACKAGE_REQUIRED_FIELDS = Object.freeze(["validator_version"]);

/**
 * Evidence-bearing supplement for HISTORICAL packages.
 *
 * Some provenance is determinable from a package's own artifacts but was never written
 * into a machine-readable field. Amending the package would change bytes that were fixed
 * at validation time, so instead the value is recorded externally together with the
 * evidence it was derived from and the date it was reconstructed. A supplemented field is
 * never reported as plain `complete`: the result is `complete_via_supplement`, so the
 * distinction between "recorded at validation time" and "reconstructed later from
 * evidence" is preserved for any reviewer.
 *
 * Every supplement entry MUST carry non-empty `evidence`. An entry without evidence is
 * rejected, because that would be indistinguishable from inventing the value.
 */
export async function loadProvenanceSupplement(supplementPath) {
  try {
    const parsed = JSON.parse(await fs.readFile(supplementPath, "utf8"));
    if (parsed?.schema_version !== PROVENANCE_SUPPLEMENT_SCHEMA_VERSION) return { entries: {} };
    return { ...parsed, entries: parsed.entries ?? {} };
  } catch {
    return { entries: {} };
  }
}

export function supplementFieldsFor(variantId, supplement) {
  const entry = supplement?.entries?.[variantId] ?? null;
  if (!entry) return {};
  const usable = {};
  for (const [field, record] of Object.entries(entry)) {
    const evidence = Array.isArray(record?.evidence) ? record.evidence.filter(Boolean) : [];
    if (record?.value == null || evidence.length === 0) continue;
    usable[field] = record;
  }
  return usable;
}

/**
 * Required provenance fields for any NEW strict variant package.
 * `resolver` reads the value from existing artifacts where one exists.
 */
export const REQUIRED_PROVENANCE_FIELDS = Object.freeze([
  { key: "base_project", description: "Defects4J project id" },
  { key: "base_bug_id", description: "Defects4J bug id" },
  { key: "base_revision", description: "exact fixed revision the variant was built from" },
  { key: "variant_id", description: "canonical variant id" },
  { key: "semantic_target_depth", description: "the depth level the construction targeted" },
  { key: "audited_semantic_depth", description: "units the shortest-path audit defends" },
  { key: "semantic_audit_id", description: "identifier of the audit record backing that number" },
  { key: "source_patch_sha256", description: "sha256 of variant.patch" },
  { key: "test_patch_sha256", description: "sha256 of test.patch" },
  { key: "source_hashes", description: "recorded source hash artifact" },
  { key: "validation_timestamp", description: "when validation actually ran" },
  { key: "validator_version", description: "the validation procedure/tool version used" },
  { key: "validation_results", description: "the recorded gate outcome" },
  { key: "reproducibility_results", description: "the recorded fresh-reproduction outcome" },
  { key: "benchmark_eligibility", description: "eligibility decision at packaging time" },
  { key: "evidence_policy_version", description: "agent-visible failure-evidence policy in force" },
  { key: "prompt_version", description: "frozen localization prompt version" },
  { key: "prompt_sha256", description: "frozen base prompt hash" },
  { key: "construction_provenance", description: "how the package was produced and by what procedure" },
]);

/** Values that look filled in but carry no information. */
function isPlaceholder(value) {
  if (value == null) return true;
  if (typeof value === "string") {
    const text = value.trim();
    if (!text) return true;
    if (/^(tbd|todo|n\/a|unknown|placeholder|none)$/i.test(text)) return true;
  }
  if (Array.isArray(value) && value.length === 0) return true;
  if (typeof value === "object" && !Array.isArray(value) && Object.keys(value).length === 0) return true;
  return false;
}

/**
 * A timestamp of exactly midnight, or on the hour with zero seconds, is very likely a
 * nominal value typed by hand rather than emitted by the validation run. This is flagged,
 * not failed: it is a provenance-quality signal.
 */
export function looksLikeNominalTimestamp(value) {
  const text = String(value ?? "");
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?$/.test(text)) return false;
  return /T\d{2}:00:00(?:\.0+)?Z?$/.test(text);
}

async function sha256OfFile(filePath) {
  try {
    return crypto.createHash("sha256").update(await fs.readFile(filePath)).digest("hex");
  } catch {
    return null;
  }
}

/**
 * Derives whatever provenance CAN be read from an existing package. Anything absent is
 * returned as null and reported as a gap; no value is synthesised.
 */
export async function deriveVariantProvenance(
  record,
  {
    promptVersion = null,
    promptHash = null,
    depthAudit = null,
    legacyEvidencePolicyVersion = null,
    supplement = null,
  } = {},
) {
  const manifest = record?.manifest ?? {};
  const validation = record?.validation ?? null;
  const dir = record?.dir ?? "";

  const [variantPatchSha, testPatchSha] = await Promise.all([
    dir ? sha256OfFile(path.join(dir, "variant.patch")) : null,
    dir ? sha256OfFile(path.join(dir, "test.patch")) : null,
  ]);

  let sourceHashes = null;
  try {
    sourceHashes = JSON.parse(await fs.readFile(path.join(dir, "source_hashes.json"), "utf8"));
  } catch {
    sourceHashes = null;
  }

  const validationTimestamp =
    validation?.completed_at ??
    validation?.validated_at ??
    manifest.validation?.validated_at ??
    manifest.reproducibility?.reproduced_at ??
    null;

  const base = {
    schema_version: VARIANT_PROVENANCE_SCHEMA_VERSION,
    base_project: manifest.source?.defects4j_project ?? null,
    base_bug_id: manifest.source?.defects4j_bug_id ?? null,
    base_revision: manifest.source?.fixed_revision ?? manifest.source?.baseline_version ?? null,
    variant_id: manifest.variant_id ?? null,
    semantic_target_depth: manifest.reasoning?.level ?? null,
    audited_semantic_depth: depthAudit?.audited_semantic_depth ?? null,
    semantic_audit_id: depthAudit?.depth_audit_report ?? null,
    source_patch_sha256: variantPatchSha,
    test_patch_sha256: testPatchSha,
    source_hashes: sourceHashes
      ? {
          schema_version: sourceHashes.schema_version ?? null,
          hashed_file_count:
            sourceHashes.fixed_baseline?.file_count ??
            (sourceHashes.baseline ? Object.keys(sourceHashes.baseline).length : null),
          has_aggregate_digest: Boolean(sourceHashes.fixed_baseline?.aggregate_sha256),
        }
      : null,
    validation_timestamp: validationTimestamp,
    validator_version: validation?.validator_version ?? manifest.validation?.validator_version ?? null,
    validator_toolchain: validation?.validator_toolchain ?? manifest.provenance?.toolchain ?? null,
    validation_results: validation?.gate ? { status: validation.status ?? null, gate_keys: Object.keys(validation.gate) } : null,
    reproducibility_results: manifest.reproducibility ?? null,
    benchmark_eligibility: manifest.benchmark_eligible ?? null,
    // A package built before d4j-failure-evidence/v1 truthfully has no policy in force.
    // Recording that explicitly is a fact about the package, not a fabricated value;
    // `legacyEvidencePolicyVersion` is supplied by the caller so nothing is hard-coded here.
    evidence_policy_version: manifest.evidence_policy_version ?? legacyEvidencePolicyVersion ?? null,
    prompt_version: promptVersion,
    prompt_sha256: promptHash,
    construction_provenance:
      manifest.provenance ?? manifest.generation?.provenance ?? manifest.source?.artifact_path ?? null,
  };

  const supplemented = supplementFieldsFor(record?.variantId ?? manifest.variant_id, supplement);
  const appliedSupplement = {};
  for (const [field, entry] of Object.entries(supplemented)) {
    if (base[field] != null && !isPlaceholder(base[field])) continue;
    base[field] = entry.value;
    appliedSupplement[field] = {
      value: entry.value,
      evidence: entry.evidence,
      reconstructed_at: entry.reconstructed_at ?? null,
      reconstructed_by: entry.reconstructed_by ?? null,
      artifact_modified: false,
    };
  }
  base.supplemented_fields = appliedSupplement;
  return base;
}

/**
 * Validates a provenance document against the required schema.
 * `complete` means every required field is present and non-placeholder.
 */
export function validateVariantProvenance(provenance, { record = null, newArtifact = false } = {}) {
  const missing = [];
  const placeholders = [];
  for (const field of REQUIRED_PROVENANCE_FIELDS) {
    const value = provenance?.[field.key];
    if (value === undefined || value === null) missing.push(field.key);
    else if (isPlaceholder(value)) placeholders.push(field.key);
  }

  const supplementedFields = Object.keys(provenance?.supplemented_fields ?? {});
  // A NEW package must record these in the package itself; a supplement cannot stand in.
  const inPackageViolations = newArtifact
    ? IN_PACKAGE_REQUIRED_FIELDS.filter((field) => supplementedFields.includes(field))
    : [];

  const warnings = [];
  if (looksLikeNominalTimestamp(provenance?.validation_timestamp)) {
    warnings.push(
      `validation_timestamp ${provenance.validation_timestamp} is on the hour with zero seconds and is likely a nominal value rather than a tool-emitted timestamp`,
    );
  }
  if (looksLikeNominalTimestamp(provenance?.reproducibility_results?.reproduced_at)) {
    warnings.push(
      `reproducibility.reproduced_at ${provenance.reproducibility_results.reproduced_at} is likely a nominal value rather than a tool-emitted timestamp`,
    );
  }
  const hashedCount = provenance?.source_hashes?.hashed_file_count ?? null;
  if (Number.isFinite(hashedCount) && hashedCount > 0 && hashedCount < 10) {
    warnings.push(
      `source_hashes covers only ${hashedCount} file(s); comparable packages hash the full source tree with an aggregate digest`,
    );
  }
  if (provenance?.source_hashes && provenance.source_hashes.has_aggregate_digest === false) {
    warnings.push("source_hashes records no aggregate digest for the baseline tree");
  }
  if (record && record.artifactStatus && record.artifactStatus["validation.log"] === false) {
    warnings.push("validation.log is absent");
  }

  const complete = missing.length === 0 && placeholders.length === 0 && inPackageViolations.length === 0;
  return {
    schema_version: VARIANT_PROVENANCE_SCHEMA_VERSION,
    variant_id: provenance?.variant_id ?? record?.variantId ?? null,
    complete,
    // Preserves the distinction between provenance recorded at validation time and
    // provenance reconstructed later from the package's own evidence.
    completeness: !complete
      ? "incomplete"
      : supplementedFields.length
        ? "complete_via_supplement"
        : "complete",
    supplemented_fields: supplementedFields,
    in_package_required_violations: inPackageViolations,
    missing_fields: missing,
    placeholder_fields: placeholders,
    warnings,
    required_field_count: REQUIRED_PROVENANCE_FIELDS.length,
    present_field_count: REQUIRED_PROVENANCE_FIELDS.length - missing.length - placeholders.length,
  };
}
