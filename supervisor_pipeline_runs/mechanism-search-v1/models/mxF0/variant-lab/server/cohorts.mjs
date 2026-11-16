/**
 * Explicit cohort registry (issues F-8 and F-9).
 *
 * Two different family sets were previously hard-coded side by side in
 * accuracyStore.mjs and consumed implicitly:
 *
 *   ACCURACY_FAMILIES            - 9 families, drives summary/depth_summary/matrix
 *   SEVEN_FAMILY_PILOT_FAMILIES  - 7 families, drives cohort_summaries.seven_family_pilot
 *
 * They are NOT the same set: Csv-1 and Lang-1 have completed runs but sit outside the
 * default cohort, while Gson-1 and Time-1 sit inside it but outside the pilot. A reader
 * comparing "L10 Acc@1 = 0.875" against "L10 Acc@1 = 0.857" is comparing two different
 * populations. `Chart-2` is also declared in the default cohort but has no manifest and
 * no run, so it appears in family tables as an all-N/A placeholder.
 *
 * This module makes every cohort an explicit, named, documented object, requires callers
 * to name the cohort they mean, and refuses to combine cohorts that measure different
 * constructs.
 */

export const COHORT_REGISTRY_SCHEMA_VERSION = "d4j-cohort-registry/v1";

/** What a depth label means inside a cohort. */
export const DEPTH_BASIS = Object.freeze({
  /** Level labels are taken from manifests as declared. Historical results use this. */
  NOMINAL: "nominal_declared_depth",
  /** Level labels must be backed by an audited semantic depth meeting the strict bound. */
  STRICT: "audited_semantic_depth",
});

const FAMILY = (project, bugId) => ({ project, bug_id: bugId });

export const COHORTS = Object.freeze({
  "historical-default-v1": {
    cohort_id: "historical-default-v1",
    label: "Historical default accuracy cohort",
    depth_basis: DEPTH_BASIS.NOMINAL,
    families: [
      FAMILY("Chart", 1),
      FAMILY("Chart", 2),
      FAMILY("Math", 1),
      FAMILY("Cli", 1),
      FAMILY("Collections", 1),
      FAMILY("Codec", 1),
      FAMILY("Gson", 1),
      FAMILY("Time", 1),
      FAMILY("Closure", 1),
    ],
    excluded_families: ["Csv-1", "Lang-1"],
    inclusion_criteria: [
      "family is listed above",
      "run task maps to a canonical cell in a batch manifest",
      "cell availability is 'available'",
      `prompt version is the frozen ${"d4j-localization-only/v2"}`,
      "prompt base hash is the frozen hash",
      "run status is completed with a parsed 10-prediction ranking",
    ],
    exclusion_criteria: [
      "Csv-1 and Lang-1 completed runs: observed in earlier batches, outside this cohort",
      "runs with an unfrozen prompt version or hash",
      "non-completed runs (provider_error, failed, invalid_ranking, protocol_error)",
      "tasks whose cell availability is generation_failed / depth_unachievable / dependency_skipped / validation_failed",
    ],
    notes:
      "Chart-2 is declared but has no variant manifest and no run. It appears as an all-N/A placeholder row and contributes nothing to any denominator. Declared depth is taken at face value: this cohort does NOT verify audited semantic depth.",
    supports_strict_depth_claims: false,
  },
  "seven-family-l10-l90-v1": {
    cohort_id: "seven-family-l10-l90-v1",
    label: "Seven-family L10-L90 depth pilot",
    depth_basis: DEPTH_BASIS.NOMINAL,
    families: [
      FAMILY("Chart", 1),
      FAMILY("Math", 1),
      FAMILY("Cli", 1),
      FAMILY("Collections", 1),
      FAMILY("Codec", 1),
      FAMILY("Closure", 1),
      FAMILY("Csv", 1),
    ],
    excluded_families: ["Chart-2", "Gson-1", "Time-1", "Lang-1"],
    inclusion_criteria: [
      "family is listed above",
      "run is registered in the seven-family-l10-l90-v1 batch manifest",
      "frozen prompt version and hash",
      "completed run with a parsed 10-prediction ranking",
    ],
    exclusion_criteria: [
      "Gson-1 and Time-1: completed, but not selected for this pilot",
      "Lang-1: earlier batch only",
      "Math L70: completed but benchmark-ineligible after shortest-path review",
    ],
    notes:
      "One eligible run per executable condition (n=1 per cell). Descriptive only. Depth labels are nominal.",
    supports_strict_depth_claims: false,
  },
  "multi-family-l10-l30-l50-v1": {
    cohort_id: "multi-family-l10-l30-l50-v1",
    label: "Earlier nine-family L10/L30/L50 batch",
    depth_basis: DEPTH_BASIS.NOMINAL,
    families: [
      FAMILY("Cli", 1),
      FAMILY("Collections", 1),
      FAMILY("Math", 1),
      FAMILY("Lang", 1),
      FAMILY("Csv", 1),
      FAMILY("Codec", 1),
      FAMILY("Gson", 1),
      FAMILY("Time", 1),
      FAMILY("Closure", 1),
    ],
    excluded_families: ["Chart-1", "Chart-2"],
    inclusion_criteria: ["family is listed above", "run is registered in the multi-family-l10-l30-l50-v1 batch manifest"],
    exclusion_criteria: [
      "Chart-1: not part of this batch",
      "shares canonical run artifacts with the seven-family pilot; its rows are the SAME runs, not repetitions",
    ],
    notes:
      "Predates the seven-family selection. Must never be added to the seven-family pilot as independent repetitions - the underlying run directories overlap.",
    supports_strict_depth_claims: false,
  },
  "closure-name-ablation-v1": {
    cohort_id: "closure-name-ablation-v1",
    label: "Closure-1 method-name ablation pilot",
    depth_basis: DEPTH_BASIS.NOMINAL,
    families: [FAMILY("Closure", 1)],
    excluded_families: ["all other families"],
    inclusion_criteria: [
      "paired control and name-ablated Closure-1 variants at L10, L30, L50",
      "control-first execution order",
      "frozen prompt, model and 50/5/300 budget",
    ],
    exclusion_criteria: [
      "not part of the 53-run accuracy aggregation",
      "the L50 control rerun here (gold rank 3) is a DIFFERENT run from the aggregation's Closure L50 row (gold rank 2); the two must never be merged",
    ],
    notes:
      "n=1 per depth per condition. All three depths are nominal; the audited depths are 7, 9 and 12 respectively.",
    supports_strict_depth_claims: false,
  },
  "strict-chart-closure-l10-l30-v1": {
    cohort_id: "strict-chart-closure-l10-l30-v1",
    label: "Strict audited-depth Chart-1 / Closure-1 L10-L30 cohort",
    depth_basis: DEPTH_BASIS.STRICT,
    families: [FAMILY("Chart", 1), FAMILY("Closure", 1)],
    excluded_families: ["every other family"],
    inclusion_criteria: [
      "variant has depth_audit_status = audited_strict_pass in depth-audit-registry.json",
      "audited_semantic_depth meets the strict lower bound for its level",
      "artifact consistency is fully_verified with structural method verification",
      `evidence policy version is ${"d4j-failure-evidence/v1"} and compliance is ok`,
      "frozen prompt version and hash",
    ],
    exclusion_criteria: [
      "every nominal-only or unaudited artifact, including all existing L50/L70 packages",
      "every historical run, all of which predate the evidence policy",
      "CLOSURE-1-L10-001 (audited 7 < 10)",
      "CHART-1-L10-SECONDARY-02 (audited 8 < 10) and CHART-1-L30-001 (audited 12 < 30)",
    ],
    notes:
      "Contains zero runs today. No historical run can ever enter it, because legacy runs carry no evidence-policy version. This is intentional: strict results must be produced under the strict protocol, never retrofitted.",
    supports_strict_depth_claims: true,
  },
});

export const DEFAULT_COHORT_ID = "historical-default-v1";

export function listCohorts() {
  return Object.values(COHORTS);
}

export function getCohort(cohortId) {
  const cohort = COHORTS[String(cohortId ?? "")];
  if (!cohort) {
    throw new Error(
      `Unknown cohort id "${cohortId}". Accuracy aggregation requires an explicit cohort id. Known cohorts: ${Object.keys(COHORTS).join(", ")}`,
    );
  }
  return cohort;
}

export function cohortFamilies(cohortId) {
  return getCohort(cohortId).families;
}

export function familyIdsForCohort(cohortId) {
  return getCohort(cohortId).families.map((family) => `${family.project}-${family.bug_id}`);
}

/**
 * Refuses to combine results from cohorts that measure different constructs or
 * different populations. Prevents the accidental mixing described in F-9.
 */
export function assertCohortsCombinable(cohortIdA, cohortIdB) {
  const a = getCohort(cohortIdA);
  const b = getCohort(cohortIdB);
  if (a.cohort_id === b.cohort_id) return { ok: true, reasons: [] };
  const reasons = [];
  if (a.depth_basis !== b.depth_basis) {
    reasons.push(
      `Cohorts use different depth bases (${a.cohort_id}: ${a.depth_basis}; ${b.cohort_id}: ${b.depth_basis}); nominal and audited depths are different constructs`,
    );
  }
  const aFamilies = new Set(familyIdsForCohort(a.cohort_id));
  const bFamilies = new Set(familyIdsForCohort(b.cohort_id));
  const onlyA = [...aFamilies].filter((family) => !bFamilies.has(family));
  const onlyB = [...bFamilies].filter((family) => !aFamilies.has(family));
  if (onlyA.length || onlyB.length) {
    reasons.push(
      `Cohorts cover different families (only in ${a.cohort_id}: ${onlyA.join(", ") || "none"}; only in ${b.cohort_id}: ${onlyB.join(", ") || "none"})`,
    );
  }
  reasons.push(
    `${a.cohort_id} and ${b.cohort_id} may share underlying run directories; combining them would double-count runs rather than add repetitions`,
  );
  return { ok: false, reasons };
}

export function cohortRegistryDocument() {
  return {
    schema_version: COHORT_REGISTRY_SCHEMA_VERSION,
    default_cohort_id: DEFAULT_COHORT_ID,
    cohorts: listCohorts(),
  };
}
