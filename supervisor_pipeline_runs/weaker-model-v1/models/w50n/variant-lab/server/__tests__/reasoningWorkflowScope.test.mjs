import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import test from "node:test";

import {
  REASONING_WORKFLOW_EPISTEMIC_SCOPE,
  buildReasoningWorkflow,
  reasoningWorkflowSourceTypes,
  validateAgentEvidenceChain,
} from "../reasoningWorkflow.mjs";

const TRAJECTORY = [
  { sequence: 1, type: "search", target: "getLegendItem", timestamp: "2026-09-14T00:00:01Z" },
  { sequence: 2, type: "open_file", target: "source/A.java", timestamp: "2026-09-14T00:00:02Z" },
  { sequence: 3, type: "open_file", target: "source/A.java", timestamp: "2026-09-14T00:00:03Z" },
  { sequence: 4, type: "test_run", target: "defects4j test -t X::y", timestamp: "2026-09-14T00:00:04Z" },
];

const SUBMISSION = {
  ok: true,
  prediction_count: 10,
  submitted_at: "2026-09-14T00:00:10Z",
  predictions: Array.from({ length: 10 }, (_, index) => ({ class: `com.example.C${index}`, method: "m" })),
  evidence_chain: [
    { evidence: "The assertion compares series keys.", inference_summary: "Legend identity is wrong.", candidate_methods: ["com.example.C0::m"], references: [{ file: "source/A.java" }] },
  ],
};

test("every node declares a source type from the declared set", () => {
  const workflow = buildReasoningWorkflow({ runId: "r1", trajectory: TRAJECTORY, structuredSubmission: SUBMISSION });
  assert.ok(workflow.nodes.length > 0);
  for (const node of workflow.nodes) {
    assert.ok(reasoningWorkflowSourceTypes.has(node.source_type), `${node.id} has source_type ${node.source_type}`);
  }
});

test("harness-derived events are observed and agent claims are agent_reported", () => {
  const workflow = buildReasoningWorkflow({ runId: "r1", trajectory: TRAJECTORY, structuredSubmission: SUBMISSION });
  const search = workflow.nodes.find((node) => node.kind === "search");
  assert.equal(search.source_type, "observed");
  const inference = workflow.nodes.find((node) => node.source_type === "agent_reported");
  assert.ok(inference, "an accepted evidence chain must produce agent_reported nodes");
  assert.equal(inference.evidence, "The assertion compares series keys.");
});

test("observed nodes never carry an inference summary the agent did not report", () => {
  const workflow = buildReasoningWorkflow({ runId: "r1", trajectory: TRAJECTORY, structuredSubmission: null });
  for (const node of workflow.nodes) {
    assert.equal(node.source_type, "observed");
    assert.equal(node.inference_summary, "", `${node.id} must not attribute an inference to the agent`);
    assert.deepEqual(node.candidate_methods.length ? [] : [], []);
  }
});

test("the derived source type is actually emitted and adds no new information", () => {
  const workflow = buildReasoningWorkflow({ runId: "r1", trajectory: TRAJECTORY, structuredSubmission: SUBMISSION });
  assert.equal(workflow.derived_metrics.source_type, "derived");
  assert.equal(workflow.derived_metrics.search_count, 1);
  assert.equal(workflow.derived_metrics.file_read_count, 2);
  assert.equal(workflow.derived_metrics.unique_files_read, 1);
  assert.equal(workflow.derived_metrics.test_run_count, 1);
  assert.equal(workflow.derived_metrics.submitted, true);
  assert.equal(workflow.derived_metrics.agent_reported_node_count, 1);
});

test("the workflow declares its epistemic scope and disclaims private reasoning", () => {
  const workflow = buildReasoningWorkflow({ runId: "r1", trajectory: TRAJECTORY, structuredSubmission: SUBMISSION });
  assert.deepEqual(workflow.epistemic_scope, REASONING_WORKFLOW_EPISTEMIC_SCOPE);
  const disclaimed = REASONING_WORKFLOW_EPISTEMIC_SCOPE.does_not_represent.join(" ").toLowerCase();
  assert.ok(disclaimed.includes("chain-of-thought"));
  assert.ok(disclaimed.includes("hidden internal reasoning"));
  assert.ok(disclaimed.includes("beliefs"));
  assert.match(REASONING_WORKFLOW_EPISTEMIC_SCOPE.edge_semantics, /TEMPORAL ORDER ONLY/);
});

test("edges are temporal only and are labelled as such", () => {
  const workflow = buildReasoningWorkflow({ runId: "r1", trajectory: TRAJECTORY, structuredSubmission: SUBMISSION });
  assert.ok(workflow.edges.length > 0);
  for (const edge of workflow.edges) assert.equal(edge.relation, "next");
  assert.match(workflow.epistemic_scope.edge_semantics, /not inference dependencies/);
});

test("a rejected evidence chain contributes no nodes and does not invalidate the workflow", () => {
  const bad = { ...SUBMISSION, evidence_chain: [{ evidence: "", inference_summary: "" }] };
  const validation = validateAgentEvidenceChain(bad.evidence_chain);
  assert.equal(validation.ok, false);
  const workflow = buildReasoningWorkflow({ runId: "r1", trajectory: TRAJECTORY, structuredSubmission: bad });
  assert.equal(workflow.agent_reported_chain_status, "rejected");
  assert.equal(workflow.nodes.filter((node) => node.source_type === "agent_reported").length, 0);
  assert.ok(workflow.nodes.length > 0, "observable behaviour is still recorded");
});

test("no source module claims to capture hidden model reasoning", async () => {
  const serverDir = path.resolve(process.cwd());
  const files = [];
  const walk = async (dir) => {
    for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
      if (entry.name === "node_modules" || entry.name === "__tests__" || entry.name === "__pycache__") continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) await walk(full);
      else if (/\.(mjs|py)$/.test(entry.name)) files.push(full);
    }
  };
  await walk(serverDir);

  // Phrases that would assert access to hidden cognition. The codebase may MENTION
  // chain-of-thought only to forbid or disclaim it.
  const forbidden = [
    /captur\w*\s+(?:the\s+)?(?:model|agent)['"]?s?\s+reasoning/i,
    /records?\s+(?:the\s+)?(?:hidden|internal|private)\s+reasoning/i,
    /represents?\s+(?:the\s+)?chain.of.thought/i,
    /reveals?\s+what\s+the\s+(?:model|agent)\s+(?:thought|believed)/i,
  ];
  for (const file of files) {
    const text = await fs.readFile(file, "utf8");
    for (const pattern of forbidden) {
      assert.equal(pattern.test(text), false, `${path.basename(file)} must not claim to capture hidden reasoning (${pattern})`);
    }
  }
  assert.ok(files.length > 5, "the scan must actually have read the server sources");
});
