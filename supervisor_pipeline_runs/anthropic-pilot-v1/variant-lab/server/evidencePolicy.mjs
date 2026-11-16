/**
 * Frozen agent-visible failure-evidence policy.
 *
 * Research motivation (issue F-2)
 * -------------------------------
 * Before this policy, the agent-visible `stack_trace` for a variant task was copied
 * verbatim from a human-authored field of the private variant manifest. In practice
 * that produced two incompatible evidence regimes in the same benchmark:
 *
 *   - 28 historical variants carried 2,848-7,389 characters (38-133 lines) of real
 *     captured `defects4j test` output;
 *   - the three strict depth artifacts carried a single ~90-character prose sentence.
 *
 * Any depth comparison spanning both regimes confounds semantic depth with the
 * quantity and kind of failure evidence supplied. This module makes the evidence
 * supplied to the agent a deterministic function of the prepared workspace rather
 * than of manifest authoring.
 *
 * The policy is frozen and versioned. Historical runs are NOT reinterpreted: runs
 * written before this module existed carry no `evidence_policy_version` and are
 * reported as LEGACY_EVIDENCE_POLICY_VERSION by downstream consumers.
 */

export const EVIDENCE_POLICY_VERSION = "d4j-failure-evidence/v1";
export const LEGACY_EVIDENCE_POLICY_VERSION = "legacy/pre-evidence-policy";
export const FAILURE_EVIDENCE_SCHEMA_VERSION = "d4j-failure-evidence-record/v1";

export const EVIDENCE_PROVENANCE = Object.freeze({
  CAPTURED: "captured_from_prepared_workspace",
  MANIFEST_RECORDED: "manifest_recorded_machine_output",
  HUMAN_SUMMARY: "manifest_human_authored_summary",
  UNAVAILABLE: "unavailable",
});

/**
 * Declarative, machine-readable statement of the frozen policy. Persisted into run
 * manifests so that any future reader can tell exactly what the agent was shown.
 */
export const failureEvidencePolicy = Object.freeze({
  policy_version: EVIDENCE_POLICY_VERSION,
  schema_version: FAILURE_EVIDENCE_SCHEMA_VERSION,
  applies_to: ["original", "variant"],
  identical_across_depths: true,
  failing_test_identifier: "exposed verbatim, exactly one identifier",
  failing_test_source:
    "extracted mechanically from the prepared agent workspace; manifest-provided source is used only when the workspace extraction returns nothing",
  stack_trace:
    "captured mechanically by executing the single allowed failing-test command inside the prepared agent workspace",
  raw_failure_output: "the captured text is the stack trace field; no second raw channel is exposed",
  human_authored_summaries: "forbidden as a substitute for captured output",
  ordering: "preserved exactly as emitted by the test command; no reordering",
  normalization: [
    "line endings normalised to LF",
    "ANSI escape sequences removed",
    "absolute workspace path replaced with <WORKSPACE>",
    "absolute repository path replaced with <REPO>",
    "paths naming private benchmark roots replaced with <REDACTED_PATH>",
    "wall-clock timestamps replaced with <TIMESTAMP>",
    "elapsed-time and duration tokens replaced with <DURATION>",
    "JVM identity hash suffixes replaced with @<OBJID>",
    "runs of four or more dots collapsed to exactly four",
    "trailing whitespace stripped per line; runs of blank lines collapsed to one",
  ],
  max_lines: 120,
  head_lines: 90,
  tail_lines: 30,
  max_chars: 8000,
  truncation: "head_and_tail",
  truncation_marker: "... [evidence truncated by d4j-failure-evidence/v1] ...",
  private_metadata_screen: "evidence is rejected if it names private benchmark infrastructure",
  natural_identifier_policy:
    "class, method and file names that occur naturally in real failure output are preserved as realistic debugging evidence and recorded as lexical-exposure covariates; they are never removed",
});

const ANSI_PATTERN = /\[[0-9;?]*[ -/]*[@-~]/g;

const PRIVATE_METADATA_TOKENS = Object.freeze([
  "new_bug_variants",
  "variant_manifest.json",
  "reasoning_tree.yaml",
  "generation_trace.json",
  "variant_report.md",
  "validation.json",
  "validation.log",
  "source_hashes.json",
  "variant.patch",
  "test.patch",
  "gold_methods",
  "gold.json",
  "faulty_method",
  "evaluation.json",
  "ranking.json",
  "run_manifest.json",
  "benchmark_runs",
]);

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function countLines(text) {
  if (!text) return 0;
  return text.split("\n").length;
}

/**
 * Deterministic normalisation. Identical input text always yields identical output,
 * independent of machine, clock, working directory or run identity.
 */
export function normalizeFailureEvidence(rawText, { workspaceRoot = "", repoRoot = "", extraRedactions = [] } = {}) {
  const applied = [];
  let text = String(rawText ?? "");
  if (!text) return { text: "", applied };

  const before = text;
  text = text.replace(/\r\n?/g, "\n");
  if (text !== before) applied.push("line_endings");

  if (ANSI_PATTERN.test(text)) {
    ANSI_PATTERN.lastIndex = 0;
    text = text.replace(ANSI_PATTERN, "");
    applied.push("ansi");
  }
  ANSI_PATTERN.lastIndex = 0;

  // Longest path first so that a workspace nested inside the repo is replaced with
  // the more specific placeholder.
  const pathReplacements = [
    [workspaceRoot, "<WORKSPACE>"],
    [repoRoot, "<REPO>"],
    ...extraRedactions.map((value) => [value, "<REDACTED_PATH>"]),
  ]
    .filter(([value]) => typeof value === "string" && value.length > 1)
    .sort((a, b) => b[0].length - a[0].length);
  for (const [value, placeholder] of pathReplacements) {
    const pattern = new RegExp(escapeRegExp(value), "g");
    if (pattern.test(text)) {
      pattern.lastIndex = 0;
      text = text.replace(pattern, placeholder);
      applied.push(`path:${placeholder}`);
    }
  }

  // Any surviving absolute path that names a private benchmark root.
  const privateRootPattern = /(?:\/[^\s:;,"')\]]*)?\/(?:new_bug_variants|benchmark_runs|variant-lab\/server)(?:\/[^\s:;,"')\]]*)?/g;
  if (privateRootPattern.test(text)) {
    privateRootPattern.lastIndex = 0;
    text = text.replace(privateRootPattern, "<REDACTED_PATH>");
    applied.push("path:private_root");
  }

  const timestampPattern =
    /\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?\b/g;
  if (timestampPattern.test(text)) {
    timestampPattern.lastIndex = 0;
    text = text.replace(timestampPattern, "<TIMESTAMP>");
    applied.push("timestamp");
  }

  const durationPattern =
    /(\bTime:\s*)[\d.,]+\b|\b\d+(?:\.\d+)?\s*(?:ms|msec|sec|secs|seconds|s)\b(?=[\s)\].,]|$)|\(\s*[\d.,]+\s*(?:ms|sec|secs|seconds|s)\s*\)/gi;
  if (durationPattern.test(text)) {
    durationPattern.lastIndex = 0;
    text = text.replace(durationPattern, (match, timePrefix) => (timePrefix ? `${timePrefix}<DURATION>` : "<DURATION>"));
    applied.push("duration");
  }

  const objectIdPattern = /@[0-9a-f]{6,}\b/gi;
  if (objectIdPattern.test(text)) {
    objectIdPattern.lastIndex = 0;
    text = text.replace(objectIdPattern, "@<OBJID>");
    applied.push("object_identity");
  }

  const dotsPattern = /\.{4,}/g;
  if (dotsPattern.test(text)) {
    dotsPattern.lastIndex = 0;
    text = text.replace(dotsPattern, "....");
    applied.push("dot_padding");
  }

  text = text
    .split("\n")
    .map((line) => line.replace(/[ \t]+$/, ""))
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/^\n+/, "")
    .replace(/\n+$/, "");
  applied.push("whitespace");

  return { text, applied };
}

/**
 * Head-and-tail truncation with an explicit marker. Applied identically to every
 * condition so that long and short natural outputs converge on the same budget.
 */
export function truncateFailureEvidence(text, policy = failureEvidencePolicy) {
  const source = String(text ?? "");
  const originalLineCount = source ? countLines(source) : 0;
  const originalCharCount = source.length;
  let lines = source ? source.split("\n") : [];
  let truncated = false;
  let omittedLines = 0;

  if (lines.length > policy.max_lines) {
    const head = lines.slice(0, policy.head_lines);
    const tail = lines.slice(lines.length - policy.tail_lines);
    omittedLines = lines.length - head.length - tail.length;
    lines = [...head, policy.truncation_marker, ...tail];
    truncated = true;
  }

  let result = lines.join("\n");
  if (result.length > policy.max_chars) {
    // Trim from the tail, never from the head: the assertion and failure summary sit
    // at the top of Defects4J output and are the scientifically load-bearing part.
    const keep = Math.max(0, policy.max_chars - policy.truncation_marker.length - 1);
    result = `${result.slice(0, keep).replace(/\n[^\n]*$/, "")}\n${policy.truncation_marker}`;
    truncated = true;
  }

  return {
    text: result,
    truncated,
    original_line_count: originalLineCount,
    original_char_count: originalCharCount,
    omitted_lines: omittedLines,
    final_line_count: result ? countLines(result) : 0,
    final_char_count: result.length,
  };
}

/**
 * Distinguishes real captured test output from a human-authored description.
 *
 * A human summary such as
 *   "ComparisonFailure in CategoryPlotTests.testGeneratedItemMetadata; no gold method appears."
 * mentions a JUnit type but has no structural evidence, so keyword presence alone is
 * deliberately NOT sufficient.
 */
export function classifyEvidenceProvenanceText(text) {
  const value = String(text ?? "").trim();
  if (!value) return "empty";
  const lineCount = countLines(value);
  const hasFailingTestsHeader = /^\s*Failing tests:\s*\d+\s*$/m.test(value);
  const hasStackFrame = /^\s+at\s+[A-Za-z_$][\w$.]*(?:\.[A-Za-z_$][\w$]*)*\s*\([^)]*\)/m.test(value);
  const hasExpectedActualBlock =
    /^\s*(?:Expected|Result|Actual)\s*:/m.test(value) ||
    /expected:\s*<.*?>\s*but was:\s*<.*?>/i.test(value) ||
    /^\s*(?:Expected|Result):\s*\S/m.test(value);
  // A genuine JUnit failure can be as short as three lines (assertion + one frame),
  // so there is no minimum-length rule. What separates captured output from prose is
  // STRUCTURE: a real stack frame, the Defects4J failing-test header, or an
  // expected/actual block. Merely naming a JUnit type is not sufficient - the
  // rejected strict-artifact summaries all name one.
  if (hasStackFrame) return "machine_generated";
  if (hasFailingTestsHeader) return "machine_generated";
  if (hasExpectedActualBlock && lineCount >= 3) return "machine_generated";
  return "human_authored_summary";
}

export function screenEvidenceForPrivateMetadata(text) {
  const value = String(text ?? "");
  const hits = PRIVATE_METADATA_TOKENS.filter((token) => value.includes(token));
  return { ok: hits.length === 0, hits };
}

/**
 * Builds the single canonical evidence record for one benchmark task.
 *
 * `capturedText` is output obtained mechanically from the prepared workspace.
 * `manifestText` is whatever the private manifest recorded; it is used only as a
 * fallback, and only when it is itself machine-generated output.
 */
export function buildFailureEvidence({
  capturedText = "",
  manifestText = "",
  failingTestIdentifier = "",
  allowedTestCommand = "",
  workspaceRoot = "",
  repoRoot = "",
  captureError = null,
  policy = failureEvidencePolicy,
} = {}) {
  const capturedClass = classifyEvidenceProvenanceText(capturedText);
  const manifestClass = classifyEvidenceProvenanceText(manifestText);

  let provenance = EVIDENCE_PROVENANCE.UNAVAILABLE;
  let selected = "";
  if (capturedClass === "machine_generated") {
    provenance = EVIDENCE_PROVENANCE.CAPTURED;
    selected = capturedText;
  } else if (manifestClass === "machine_generated") {
    provenance = EVIDENCE_PROVENANCE.MANIFEST_RECORDED;
    selected = manifestText;
  } else if (manifestClass === "human_authored_summary") {
    provenance = EVIDENCE_PROVENANCE.HUMAN_SUMMARY;
    selected = "";
  }

  const normalized = normalizeFailureEvidence(selected, { workspaceRoot, repoRoot });
  const truncation = truncateFailureEvidence(normalized.text, policy);
  const screen = screenEvidenceForPrivateMetadata(truncation.text);
  const text = screen.ok ? truncation.text : "";

  return {
    schema_version: policy.schema_version,
    evidence_policy_version: policy.policy_version,
    failing_test_identifier: String(failingTestIdentifier ?? ""),
    allowed_test_command: String(allowedTestCommand ?? ""),
    provenance,
    captured_classification: capturedClass,
    manifest_classification: manifestClass,
    capture_error: captureError ? String(captureError) : null,
    normalizations_applied: normalized.applied,
    truncated: truncation.truncated,
    original_line_count: truncation.original_line_count,
    original_char_count: truncation.original_char_count,
    omitted_lines: truncation.omitted_lines,
    line_count: screen.ok ? truncation.final_line_count : 0,
    char_count: text.length,
    private_metadata_screen: screen,
    text,
  };
}

/**
 * Strict-cohort compliance. This gate is consulted by the research-validity preflight;
 * it deliberately does NOT silently downgrade a run, because a non-compliant condition
 * must be visible before an experiment starts rather than explained afterwards.
 */
export function evidencePolicyCompliance(record, policy = failureEvidencePolicy) {
  const reasons = [];
  if (!record || typeof record !== "object") {
    return { ok: false, reasons: ["No failure-evidence record is present"] };
  }
  if (record.evidence_policy_version !== policy.policy_version) {
    reasons.push(`Evidence policy version is ${record.evidence_policy_version ?? "absent"}, expected ${policy.policy_version}`);
  }
  if (record.provenance === EVIDENCE_PROVENANCE.HUMAN_SUMMARY) {
    reasons.push("Failure evidence is a human-authored summary, which the frozen policy forbids");
  }
  if (record.provenance === EVIDENCE_PROVENANCE.UNAVAILABLE) {
    reasons.push("No machine-generated failure evidence is available for this condition");
  }
  if (!record.failing_test_identifier) reasons.push("Failing test identifier is missing");
  if (!record.private_metadata_screen?.ok) {
    reasons.push(`Failure evidence names private benchmark metadata: ${(record.private_metadata_screen?.hits ?? []).join(", ")}`);
  }
  if (!record.text) reasons.push("Agent-visible failure evidence is empty");
  return { ok: reasons.length === 0, reasons };
}

/**
 * Two conditions whose underlying failure outputs are equivalent must receive
 * byte-identical agent-visible evidence formatting. Used by tests and by the
 * research-validity preflight.
 */
export function evidenceFormattingEquivalent(recordA, recordB) {
  const shapeOf = (record) => ({
    policy: record?.evidence_policy_version ?? null,
    provenance: record?.provenance ?? null,
    truncated: record?.truncated ?? null,
    normalizations: [...(record?.normalizations_applied ?? [])].sort().join(","),
    text: record?.text ?? null,
  });
  const a = shapeOf(recordA);
  const b = shapeOf(recordB);
  const differences = Object.keys(a).filter((key) => a[key] !== b[key]);
  return { equivalent: differences.length === 0, differences };
}

export function evidencePolicyVersionForManifest(manifest) {
  const value = manifest?.evidence?.evidence_policy_version ?? manifest?.evidence_policy_version ?? null;
  return value || LEGACY_EVIDENCE_POLICY_VERSION;
}
