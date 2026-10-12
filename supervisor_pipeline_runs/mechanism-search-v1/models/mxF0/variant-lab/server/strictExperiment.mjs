/**
 * Declarative specification of the next strict depth experiment.
 *
 * Kept in code so that the preflight, the CLI and any future runner all read the same
 * condition list, and so that a new experiment cannot silently reuse an old id.
 *
 * NOTHING here launches anything.
 */

export const STRICT_EXPERIMENT_ID = "strict-chart-closure-l10-l30-v1";
export const STRICT_EXPERIMENT_COHORT_ID = "strict-chart-closure-l10-l30-v1";

/** The historical stop record that must never be reused or overwritten. */
export const SUPERSEDED_EXPERIMENT_IDS = Object.freeze(["chart-closure-l10-l30-pilot"]);

export const STRICT_EXPERIMENT_BUDGET = Object.freeze({
  max_tool_calls: 50,
  max_test_runs: 5,
  timeout_seconds: 300,
  agent_startup_timeout_seconds: 30,
  repeats: 1,
});

export const STRICT_EXPERIMENT_CONDITIONS = Object.freeze([
  { arm: "Chart-1 Original", order: 1, task_type: "original", project: "Chart", bug_id: 1, shortcut_risk: "unassessed" },
  {
    arm: "Chart-1 strict L10",
    order: 2,
    task_type: "variant",
    variant_id: "CHART-1-L10-STRICT-001",
    required_level: "L10",
    shortcut_risk: "medium",
  },
  {
    arm: "Chart-1 strict L30",
    order: 3,
    task_type: "variant",
    variant_id: "CHART-1-L30-DEPENDENCY-001",
    required_level: "L30",
    shortcut_risk: "high",
  },
  { arm: "Closure-1 Original", order: 4, task_type: "original", project: "Closure", bug_id: 1, shortcut_risk: "unassessed" },
  {
    arm: "Closure-1 strict L10",
    order: 5,
    task_type: "variant",
    // CLOSURE-1-L10-001 audits to 7 < 10 and must NOT be substituted here. The strict
    // replacement was constructed and fully validated on 2026-09-14; see
    // closure-l10-strict-design-spec.md and the package's own validation.log.
    variant_id: "CLOSURE-1-L10-STRICT-001",
    required_level: "L10",
    shortcut_risk: "low",
  },
  {
    arm: "Closure-1 strict L30",
    order: 6,
    task_type: "variant",
    variant_id: "CLOSURE-1-L30-STRICT-001",
    required_level: "L30",
    shortcut_risk: "low",
  },
]);

/** The subset that is fully ready today, for a reduced within-family pilot. */
export const CHART_ONLY_REDUCED_CONDITIONS = Object.freeze(
  STRICT_EXPERIMENT_CONDITIONS.filter((condition) => condition.arm.startsWith("Chart-1")),
);
