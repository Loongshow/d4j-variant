export const REASONING_WORKFLOW_SCHEMA_VERSION = "d4j-reasoning-workflow/v1";

export const reasoningWorkflowSourceTypes = new Set(["observed", "agent_reported", "derived"]);

/**
 * Explicit epistemic scope (issue: observable workflow vs private chain-of-thought).
 *
 * This structure is a record of OBSERVABLE BEHAVIOUR. It is emitted with every workflow
 * document so that no downstream reader - human or tool - can mistake it for a record of
 * the model's reasoning.
 */
export const REASONING_WORKFLOW_EPISTEMIC_SCOPE = Object.freeze({
  represents: [
    "tool calls issued by the agent",
    "repository searches",
    "file reads",
    "test executions",
    "the structured final submission",
    "the observable order of those events",
    "concise evidence the agent chose to report through submit_fault_localization",
  ],
  does_not_represent: [
    "private chain-of-thought",
    "hidden internal reasoning",
    "model beliefs, intentions or confidence",
    "why an action was taken",
    "any inference the agent did not explicitly report",
  ],
  source_types: {
    observed: "derived by the harness from the agent process; the agent cannot author these",
    agent_reported:
      "supplied by the agent through the structured submission tool; self-reported, unverified, and NOT evidence of hidden cognition",
    derived: "computed by the harness from observed events; contains no new information",
  },
  edge_semantics:
    "edges with relation 'next' encode TEMPORAL ORDER ONLY. They are not inference dependencies and must not be read as a reasoning chain.",
  interpretation_rules: [
    "A search for the gold method name may be a consequence of having already found it; it is not proof of prior lexical leakage.",
    "The absence of a search does not prove the absence of lexical use.",
    "An accepted agent_reported evidence chain is a claim by the agent, not a verified account of its reasoning.",
    "A rejected or absent evidence chain says nothing about localization quality; transport and evidence are decoupled.",
  ],
});

const eventKindMap = {
  test_run: "test_run",
  search: "search",
  open_file: "file_read",
  submission: "final_submission",
  command: "evidence",
  other: "evidence",
};

function normalizeReferences(value) {
  if (!Array.isArray(value)) return [];
  return value.map((reference) => ({
    file: String(reference?.file ?? ""),
    line_start: Number.isInteger(reference?.line_start) ? reference.line_start : null,
    line_end: Number.isInteger(reference?.line_end) ? reference.line_end : null,
    trajectory_event_ids: Array.isArray(reference?.trajectory_event_ids)
      ? reference.trajectory_event_ids.map(String)
      : [],
  }));
}

function normalizeCandidateMethods(value) {
  if (!Array.isArray(value)) return [];
  const seen = new Set();
  return value
    .map((candidate) => String(candidate ?? "").trim())
    .filter((candidate) => candidate && !seen.has(candidate) && seen.add(candidate));
}

export function validateAgentEvidenceChain(value) {
  if (value == null) return { ok: true, chain: [], errors: [] };
  if (!Array.isArray(value)) {
    return { ok: false, chain: [], errors: ["evidence_chain must be an array when provided"] };
  }
  const errors = [];
  const chain = value.slice(0, 20).map((item, index) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      errors.push(`evidence_chain item ${index + 1} must be an object`);
      return {
        evidence: "",
        inference_summary: "",
        candidate_methods: [],
        references: [],
      };
    }
    const evidence = String(item.evidence ?? "").trim();
    const inferenceSummary = String(item.inference_summary ?? "").trim();
    if (!evidence && !inferenceSummary) {
      errors.push(`evidence_chain item ${index + 1} must include evidence or inference_summary`);
    }
    return {
      evidence,
      inference_summary: inferenceSummary,
      candidate_methods: normalizeCandidateMethods(item.candidate_methods),
      references: normalizeReferences(item.references),
    };
  });
  if (value.length > 20) errors.push("evidence_chain may contain at most 20 items");
  return { ok: errors.length === 0, chain, errors };
}

function observedAction(event) {
  const kind = eventKindMap[event.type] ?? "evidence";
  if (kind === "test_run") return "Reproduced or inspected the failing test";
  if (kind === "search") return "Searched the repository";
  if (kind === "file_read") return "Inspected a repository file";
  if (kind === "final_submission") return "Submitted the final Top-10 ranking";
  return "Ran an investigation command";
}

function referenceForEvent(event, eventId) {
  if (event.type !== "open_file" || !event.target) return [];
  return [{ file: String(event.target), line_start: null, line_end: null, trajectory_event_ids: [eventId] }];
}

export function buildReasoningWorkflow({ runId, trajectory = [], structuredSubmission = null, createdAt = null }) {
  const nodes = [];
  const initialTimestamp = trajectory[0]?.timestamp ?? createdAt ?? new Date().toISOString();
  nodes.push({
    id: "step-001",
    sequence: 1,
    timestamp: initialTimestamp,
    kind: "initial_evidence",
    event_type: "initial_evidence",
    source_type: "observed",
    action: "Received the failing test identifier, source, and failing output",
    evidence: "Initial task evidence supplied by the benchmark harness.",
    inference_summary: "",
    candidate_methods: [],
    references: [],
    file: null,
    command: null,
  });

  for (const event of trajectory) {
    const eventId = `trajectory-${String(event.sequence ?? nodes.length).padStart(3, "0")}`;
    nodes.push({
      id: `step-${String(nodes.length + 1).padStart(3, "0")}`,
      sequence: nodes.length + 1,
      timestamp: event.timestamp ?? initialTimestamp,
      kind: eventKindMap[event.type] ?? "evidence",
      event_type: event.type ?? "other",
      source_type: "observed",
      action: observedAction(event),
      evidence: String(event.target ?? ""),
      inference_summary: "",
      candidate_methods: [],
      references: referenceForEvent(event, eventId),
      file: event.type === "open_file" ? String(event.target ?? "") : null,
      command: event.type === "open_file" ? null : String(event.target ?? "") || null,
    });
  }

  const chainValidation = validateAgentEvidenceChain(structuredSubmission?.evidence_chain);
  if (chainValidation.ok) {
    for (const item of chainValidation.chain) {
      nodes.push({
        id: `step-${String(nodes.length + 1).padStart(3, "0")}`,
        sequence: nodes.length + 1,
        timestamp: structuredSubmission?.submitted_at ?? initialTimestamp,
        kind: item.candidate_methods.length ? "candidate_update" : "inference",
        event_type: item.candidate_methods.length ? "candidate_update" : "inference",
        source_type: "agent_reported",
        action: item.candidate_methods.length ? "Updated candidate methods" : "Reported a concise inference",
        evidence: item.evidence,
        inference_summary: item.inference_summary,
        candidate_methods: item.candidate_methods,
        references: item.references,
        file: item.references[0]?.file || null,
        command: null,
      });
    }
  }

  const finalSubmission = nodes.findLast((node) => node.kind === "final_submission");
  if (structuredSubmission?.ok && !finalSubmission) {
    nodes.push({
      id: `step-${String(nodes.length + 1).padStart(3, "0")}`,
      sequence: nodes.length + 1,
      timestamp: structuredSubmission.submitted_at ?? initialTimestamp,
      kind: "final_submission",
      event_type: "submission",
      source_type: "observed",
      action: "Submitted the final Top-10 ranking",
      evidence: `${structuredSubmission.prediction_count ?? 0} schema-validated production methods submitted.`,
      inference_summary: "",
      candidate_methods: (structuredSubmission.predictions ?? []).map(
        (prediction) => `${prediction.class}::${prediction.method}`,
      ),
      references: [],
      file: null,
      command: "submit_fault_localization",
    });
  }

  const edges = nodes.slice(1).map((node, index) => ({
    from: nodes[index].id,
    to: node.id,
    relation: "next",
  }));
  // The third declared source type is now actually emitted, so that "derived" is a real
  // category rather than an unused label. These carry no information beyond the observed
  // nodes they summarise.
  const observedNodes = nodes.filter((node) => node.source_type === "observed");
  const agentReportedNodes = nodes.filter((node) => node.source_type === "agent_reported");
  const derivedMetrics = {
    source_type: "derived",
    observed_node_count: observedNodes.length,
    agent_reported_node_count: agentReportedNodes.length,
    search_count: observedNodes.filter((node) => node.kind === "search").length,
    file_read_count: observedNodes.filter((node) => node.kind === "file_read").length,
    unique_files_read: new Set(observedNodes.filter((node) => node.file).map((node) => node.file)).size,
    test_run_count: observedNodes.filter((node) => node.kind === "test_run").length,
    submitted: observedNodes.some((node) => node.kind === "final_submission"),
  };

  return {
    schema_version: REASONING_WORKFLOW_SCHEMA_VERSION,
    run_id: runId,
    epistemic_scope: REASONING_WORKFLOW_EPISTEMIC_SCOPE,
    nodes,
    edges,
    derived_metrics: derivedMetrics,
    agent_reported_chain_status: chainValidation.ok ? "accepted" : "rejected",
    agent_reported_chain_errors: chainValidation.errors,
    generated_at: new Date().toISOString(),
  };
}

export function validateReasoningWorkflow(workflow) {
  const errors = [];
  if (workflow?.schema_version !== REASONING_WORKFLOW_SCHEMA_VERSION) errors.push("invalid schema_version");
  if (!Array.isArray(workflow?.nodes)) errors.push("nodes must be an array");
  if (!Array.isArray(workflow?.edges)) errors.push("edges must be an array");
  for (const [index, node] of (workflow?.nodes ?? []).entries()) {
    if (!reasoningWorkflowSourceTypes.has(node?.source_type)) {
      errors.push(`node ${index + 1} has invalid source_type`);
    }
    if (Number(node?.sequence) !== index + 1) errors.push(`node ${index + 1} has invalid sequence`);
  }
  return { ok: errors.length === 0, errors };
}
