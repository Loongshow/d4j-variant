import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  COHORTS,
  DEFAULT_COHORT_ID,
  DEPTH_BASIS,
  assertCohortsCombinable,
  cohortRegistryDocument,
  familyIdsForCohort,
  getCohort,
  listCohorts,
} from "../cohorts.mjs";
import {
  REQUIRED_PROVENANCE_FIELDS,
  deriveVariantProvenance,
  loadProvenanceSupplement,
  looksLikeNominalTimestamp,
  validateVariantProvenance,
} from "../variantProvenance.mjs";
import { ACCURACY_FAMILIES, SEVEN_FAMILY_PILOT_FAMILIES } from "../accuracyStore.mjs";

/* -------------------------------------------------------------------- cohorts */

test("every cohort is fully documented", () => {
  for (const cohort of listCohorts()) {
    assert.ok(cohort.cohort_id, "cohort_id");
    assert.ok(cohort.label, `${cohort.cohort_id} label`);
    assert.ok(Array.isArray(cohort.families) && cohort.families.length, `${cohort.cohort_id} families`);
    assert.ok(Array.isArray(cohort.excluded_families), `${cohort.cohort_id} excluded_families`);
    assert.ok(cohort.inclusion_criteria.length, `${cohort.cohort_id} inclusion_criteria`);
    assert.ok(cohort.exclusion_criteria.length, `${cohort.cohort_id} exclusion_criteria`);
    assert.ok(cohort.notes, `${cohort.cohort_id} notes`);
    assert.equal(typeof cohort.supports_strict_depth_claims, "boolean");
    assert.ok(Object.values(DEPTH_BASIS).includes(cohort.depth_basis));
  }
});

test("an unknown cohort id throws instead of silently defaulting", () => {
  assert.throws(() => getCohort("does-not-exist"), /Unknown cohort id/);
  assert.throws(() => getCohort(undefined), /Unknown cohort id/);
  assert.throws(() => getCohort(""), /Unknown cohort id/);
});

test("the registered cohorts match the family constants they replace", () => {
  assert.deepEqual(getCohort(DEFAULT_COHORT_ID).families, ACCURACY_FAMILIES);
  assert.deepEqual(getCohort("seven-family-l10-l90-v1").families, SEVEN_FAMILY_PILOT_FAMILIES);
});

test("F-9: the default cohort and the pilot cohort are different populations", () => {
  const defaultFamilies = new Set(familyIdsForCohort(DEFAULT_COHORT_ID));
  const pilotFamilies = new Set(familyIdsForCohort("seven-family-l10-l90-v1"));
  assert.notDeepEqual([...defaultFamilies].sort(), [...pilotFamilies].sort());
  assert.ok(pilotFamilies.has("Csv-1") && !defaultFamilies.has("Csv-1"));
  assert.ok(defaultFamilies.has("Gson-1") && !pilotFamilies.has("Gson-1"));
  assert.ok(defaultFamilies.has("Time-1") && !pilotFamilies.has("Time-1"));
});

test("F-8: Chart-2 is a declared placeholder and is documented as such", () => {
  assert.ok(familyIdsForCohort(DEFAULT_COHORT_ID).includes("Chart-2"));
  assert.match(getCohort(DEFAULT_COHORT_ID).notes, /Chart-2 is declared but has no variant manifest/);
});

test("cohorts may not be accidentally combined", () => {
  const sameCohort = assertCohortsCombinable(DEFAULT_COHORT_ID, DEFAULT_COHORT_ID);
  assert.equal(sameCohort.ok, true);

  const mixed = assertCohortsCombinable(DEFAULT_COHORT_ID, "seven-family-l10-l90-v1");
  assert.equal(mixed.ok, false);
  assert.ok(mixed.reasons.some((reason) => reason.includes("different families")));
  assert.ok(mixed.reasons.some((reason) => reason.includes("double-count")));

  const strictVsNominal = assertCohortsCombinable("strict-chart-closure-l10-l30-v1", "seven-family-l10-l90-v1");
  assert.equal(strictVsNominal.ok, false);
  assert.ok(strictVsNominal.reasons.some((reason) => reason.includes("different depth bases")));
});

test("only the strict cohort may support strict depth claims", () => {
  const strictCapable = listCohorts().filter((cohort) => cohort.supports_strict_depth_claims).map((cohort) => cohort.cohort_id);
  assert.deepEqual(strictCapable, ["strict-chart-closure-l10-l30-v1"]);
  assert.equal(getCohort("strict-chart-closure-l10-l30-v1").depth_basis, DEPTH_BASIS.STRICT);
});

test("the cohort registry document is serialisable and names its default", () => {
  const document = cohortRegistryDocument();
  assert.equal(document.default_cohort_id, DEFAULT_COHORT_ID);
  assert.equal(document.cohorts.length, Object.keys(COHORTS).length);
  assert.doesNotThrow(() => JSON.stringify(document));
});

/* ----------------------------------------------------------------- provenance */

async function writeStrictPackage(root, overrides = {}) {
  const dir = path.join(root, "pkg");
  await fs.mkdir(dir, { recursive: true });
  const manifest = {
    variant_id: "EXAMPLE-1-L30-STRICT-001",
    source: {
      defects4j_project: "Example",
      defects4j_bug_id: 1,
      fixed_revision: "1f",
      artifact_path: "new_bug_variants/Example/bug-1/L30/EXAMPLE-1-L30-STRICT-001/",
    },
    status: "validated",
    benchmark_eligible: true,
    reasoning: { level: "L30", unit_count: 30 },
    reproducibility: { status: "passed", reproduced_at: "2026-09-12T12:00:00Z" },
    ...overrides.manifest,
  };
  await fs.writeFile(path.join(dir, "variant_manifest.json"), JSON.stringify(manifest));
  await fs.writeFile(path.join(dir, "variant.patch"), "--- a/A.java\n+++ b/A.java\n");
  await fs.writeFile(path.join(dir, "test.patch"), "--- a/T.java\n+++ b/T.java\n");
  await fs.writeFile(
    path.join(dir, "source_hashes.json"),
    JSON.stringify(overrides.sourceHashes ?? { schema_version: "d4j-source-hashes/v1", baseline: { "A.java": "aa" } }),
  );
  const record = {
    dir,
    manifest,
    validation: overrides.validation ?? {
      status: "accepted",
      gate: { baseline_compile: { status: "pass" } },
      completed_at: "2026-09-12T12:00:00Z",
    },
    variantId: manifest.variant_id,
    artifactStatus: { "validation.log": true },
  };
  return record;
}

async function withTempRoot(run) {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "d4j-provenance-"));
  try {
    return await run(root);
  } finally {
    await fs.rm(root, { recursive: true, force: true });
  }
}

test("the provenance schema requires every field Part 6 lists", () => {
  const keys = REQUIRED_PROVENANCE_FIELDS.map((field) => field.key);
  for (const required of [
    "base_project",
    "base_revision",
    "base_bug_id",
    "variant_id",
    "semantic_target_depth",
    "audited_semantic_depth",
    "semantic_audit_id",
    "source_patch_sha256",
    "test_patch_sha256",
    "source_hashes",
    "validation_timestamp",
    "validator_version",
    "validation_results",
    "reproducibility_results",
    "benchmark_eligibility",
    "evidence_policy_version",
    "prompt_version",
    "prompt_sha256",
    "construction_provenance",
  ]) {
    assert.ok(keys.includes(required), `${required} must be a required provenance field`);
  }
});

test("derives provenance from a package and hashes both patches", async () => {
  await withTempRoot(async (root) => {
    const record = await writeStrictPackage(root);
    const provenance = await deriveVariantProvenance(record, {
      promptVersion: "d4j-localization-only/v2",
      promptHash: "abc",
      depthAudit: { audited_semantic_depth: 30, depth_audit_report: "audit.md" },
      legacyEvidencePolicyVersion: "legacy/pre-evidence-policy",
    });
    assert.equal(provenance.base_project, "Example");
    assert.equal(provenance.audited_semantic_depth, 30);
    assert.match(provenance.source_patch_sha256, /^[0-9a-f]{64}$/);
    assert.match(provenance.test_patch_sha256, /^[0-9a-f]{64}$/);
    assert.equal(provenance.evidence_policy_version, "legacy/pre-evidence-policy");
  });
});

test("a missing provenance field is reported, never invented", async () => {
  await withTempRoot(async (root) => {
    const record = await writeStrictPackage(root);
    const provenance = await deriveVariantProvenance(record, {
      promptVersion: "d4j-localization-only/v2",
      promptHash: "abc",
      depthAudit: { audited_semantic_depth: 30, depth_audit_report: "audit.md" },
      legacyEvidencePolicyVersion: "legacy/pre-evidence-policy",
    });
    const result = validateVariantProvenance(provenance, { record });
    assert.equal(result.complete, false);
    assert.deepEqual(result.missing_fields, ["validator_version"], "validator_version is the only genuinely missing field");
    assert.equal(provenance.validator_version, null, "the missing value must stay null, not be synthesised");
  });
});

test("placeholder values do not count as present", () => {
  const provenance = Object.fromEntries(REQUIRED_PROVENANCE_FIELDS.map((field) => [field.key, "value"]));
  provenance.validator_version = "TBD";
  provenance.construction_provenance = "   ";
  provenance.source_hashes = {};
  const result = validateVariantProvenance(provenance);
  assert.equal(result.complete, false);
  assert.deepEqual(result.placeholder_fields.sort(), ["construction_provenance", "source_hashes", "validator_version"]);
});

test("a fully populated provenance document validates as complete", () => {
  const provenance = Object.fromEntries(REQUIRED_PROVENANCE_FIELDS.map((field) => [field.key, "recorded"]));
  provenance.validation_timestamp = "2026-09-12T14:37:09.512Z";
  const result = validateVariantProvenance(provenance);
  assert.equal(result.complete, true);
  assert.deepEqual(result.missing_fields, []);
  assert.equal(result.present_field_count, REQUIRED_PROVENANCE_FIELDS.length);
});

test("F-6: nominal on-the-hour timestamps are flagged as provenance-quality warnings", () => {
  assert.equal(looksLikeNominalTimestamp("2026-09-12T12:00:00Z"), true);
  assert.equal(looksLikeNominalTimestamp("2026-09-12T00:00:00Z"), true);
  assert.equal(looksLikeNominalTimestamp("2026-09-04T07:48:24.396Z"), false);
  assert.equal(looksLikeNominalTimestamp("not a timestamp"), false);
});

test("F-6: a two-file source hash record is flagged against full-tree hashing", async () => {
  await withTempRoot(async (root) => {
    const record = await writeStrictPackage(root, {
      sourceHashes: { schema_version: "d4j-source-hashes/v1", baseline: { "A.java": "aa", "B.java": "bb" } },
    });
    const provenance = await deriveVariantProvenance(record, { legacyEvidencePolicyVersion: "legacy/pre-evidence-policy" });
    const result = validateVariantProvenance(provenance, { record });
    assert.ok(result.warnings.some((warning) => warning.includes("only 2 file(s)")));
    assert.ok(result.warnings.some((warning) => warning.includes("no aggregate digest")));
    assert.ok(result.warnings.some((warning) => warning.includes("nominal value")));
  });
});

/* ------------------------------------------- evidence-bearing provenance supplement */

test("a supplement fills a historical gap without modifying the artifact", async () => {
  await withTempRoot(async (root) => {
    const record = await writeStrictPackage(root);
    const supplement = {
      schema_version: "d4j-provenance-supplement/v1",
      entries: {
        "EXAMPLE-1-L30-STRICT-001": {
          validator_version: {
            value: "manual-defects4j-cli/human-operated",
            evidence: ["generation_trace.json records mode=human-only", "validation.log line 3 names the JDK"],
            reconstructed_at: "2026-09-14",
            reconstructed_by: "hardening pass",
          },
        },
      },
    };
    const before = await fs.readFile(path.join(record.dir, "variant_manifest.json"), "utf8");
    const provenance = await deriveVariantProvenance(record, {
      promptVersion: "v2",
      promptHash: "abc",
      depthAudit: { audited_semantic_depth: 30, depth_audit_report: "audit.md" },
      legacyEvidencePolicyVersion: "legacy/pre-evidence-policy",
      supplement,
    });
    const result = validateVariantProvenance(provenance, { record });

    assert.equal(provenance.validator_version, "manual-defects4j-cli/human-operated");
    assert.equal(result.complete, true);
    assert.equal(result.completeness, "complete_via_supplement", "a reconstructed field must never read as plain complete");
    assert.deepEqual(result.supplemented_fields, ["validator_version"]);
    assert.equal(provenance.supplemented_fields.validator_version.artifact_modified, false);
    assert.equal(await fs.readFile(path.join(record.dir, "variant_manifest.json"), "utf8"), before, "the artifact must be byte-identical");
  });
});

test("a supplement entry without evidence is ignored, so a value can never be invented", async () => {
  await withTempRoot(async (root) => {
    const record = await writeStrictPackage(root);
    const supplement = {
      schema_version: "d4j-provenance-supplement/v1",
      entries: { "EXAMPLE-1-L30-STRICT-001": { validator_version: { value: "made-up/v9", evidence: [] } } },
    };
    const provenance = await deriveVariantProvenance(record, { supplement, legacyEvidencePolicyVersion: "legacy/pre-evidence-policy" });
    assert.equal(provenance.validator_version, null);
    assert.deepEqual(provenance.supplemented_fields, {});
    assert.equal(validateVariantProvenance(provenance, { record }).complete, false);
  });
});

test("a supplement never overrides a value the package itself records", async () => {
  await withTempRoot(async (root) => {
    const record = await writeStrictPackage(root, {
      validation: { status: "accepted", gate: { baseline_compile: { status: "pass" } }, completed_at: "2026-09-14T10:11:12Z", validator_version: "crflb-validate.sh/v1" },
    });
    const supplement = {
      schema_version: "d4j-provenance-supplement/v1",
      entries: { "EXAMPLE-1-L30-STRICT-001": { validator_version: { value: "should-not-win", evidence: ["x"] } } },
    };
    const provenance = await deriveVariantProvenance(record, { supplement, legacyEvidencePolicyVersion: "legacy/pre-evidence-policy" });
    assert.equal(provenance.validator_version, "crflb-validate.sh/v1");
    assert.deepEqual(provenance.supplemented_fields, {});
  });
});

test("a NEW strict artifact may not satisfy validator_version by supplement", async () => {
  await withTempRoot(async (root) => {
    const record = await writeStrictPackage(root);
    const supplement = {
      schema_version: "d4j-provenance-supplement/v1",
      entries: { "EXAMPLE-1-L30-STRICT-001": { validator_version: { value: "reconstructed", evidence: ["x"] } } },
    };
    const provenance = await deriveVariantProvenance(record, {
      promptVersion: "v2",
      promptHash: "abc",
      depthAudit: { audited_semantic_depth: 30, depth_audit_report: "audit.md" },
      legacyEvidencePolicyVersion: "legacy/pre-evidence-policy",
      supplement,
    });
    assert.equal(validateVariantProvenance(provenance, { record }).complete, true, "historical packages may use it");
    const asNew = validateVariantProvenance(provenance, { record, newArtifact: true });
    assert.equal(asNew.complete, false, "a new package must record it itself");
    assert.deepEqual(asNew.in_package_required_violations, ["validator_version"]);
  });
});

test("a malformed or absent supplement degrades to empty", async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "d4j-supplement-"));
  try {
    assert.deepEqual((await loadProvenanceSupplement(path.join(dir, "missing.json"))).entries, {});
    const bad = path.join(dir, "bad.json");
    await fs.writeFile(bad, "{ not json");
    assert.deepEqual((await loadProvenanceSupplement(bad)).entries, {});
    const wrong = path.join(dir, "wrong.json");
    await fs.writeFile(wrong, JSON.stringify({ schema_version: "other", entries: { A: {} } }));
    assert.deepEqual((await loadProvenanceSupplement(wrong)).entries, {});
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
});
