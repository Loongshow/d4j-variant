import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  DEPTH_AUDIT_METHOD,
  DEPTH_AUDIT_STATUS,
  DEPTH_AUDIT_REGISTRY_SCHEMA_VERSION,
  REASONING_TREE_FORMAT,
  STRICT_DEPTH_THRESHOLDS,
  auditReasoningTree,
  emptyDepthAuditRegistry,
  loadDepthAuditRegistry,
  parseReasoningTreeDocument,
  resolveDepthAudit,
  strictDepthEligibility,
  strictDepthVerdict,
} from "../semanticDepth.mjs";

const DAG_TREE = `schema_version: d4j-reasoning-tree/v1
variant_id: EXAMPLE-1-L30-001
level: L30
unit_count: 5
semantic_root: Something must be established.
gold:
  class: com.example.Widget
  method: doWork
semantic_units:
  - {id: K01, inference: "First independent fact, with a comma.", depends_on: [], evidence: [test.patch], role: "Root."}
  - {id: K02, inference: "Second independent fact.", depends_on: [], evidence: [test.patch], role: "Root."}
  - {id: K03, inference: "Joins the two roots.", depends_on: [K01, K02], evidence: [src/A.java], role: "Join."}
  - {id: K04, inference: "Branches off K01.", depends_on: [K01], evidence: [src/A.java], role: "Branch."}
  - {id: K05, inference: "Final join.", depends_on: [K03, K04], evidence: [src/B.java], role: "Join."}
`;

const BLOCK_TREE = `schema_version: d4j-reasoning-tree/v1
variant_id: EXAMPLE-1-L10-001
level: L10
unit_count: 2
semantic_units:
  - id: C01
    inference: The configured dataset is non-null.
    depends_on: []
    evidence: [test.patch]
    role: Excludes the null-dataset failure.
  - id: C02
    inference: The renderer index is resolved correctly.
    depends_on: [C01]
    evidence: [test.patch]
    role: Establishes the slot.
`;

const JSON_LINEAR_TREE = JSON.stringify(
  {
    reasoning_level: "L10",
    semantic_inference_steps: 3,
    shortest_reasoning_path: ["First step.", "Second step.", "Third step."],
  },
  null,
  2,
);

const CATEGORIZED_TREE = `schema_version: d4j-reasoning-tree/v1
variant_id: CHART-1-L10-OLD
level: L10
unit_count: 4
root:
  R: Legend labels should describe the assigned dataset.
conditions:
  C1: The plot has a primary dataset.
  C2: The plot has a secondary dataset.
observable:
  O1: The label is Primary instead of Secondary.
`;

/* ------------------------------------------------------------------- parsing */

test("parses a flow-style semantic-unit DAG including commas inside quoted inferences", () => {
  const document = parseReasoningTreeDocument(DAG_TREE);
  assert.equal(document.format, REASONING_TREE_FORMAT.UNIT_DAG);
  assert.equal(document.declared_level, "L30");
  assert.equal(document.declared_unit_count, 5);
  assert.equal(document.units.length, 5);
  assert.equal(document.units[0].inference, "First independent fact, with a comma.");
  assert.deepEqual(document.units[2].depends_on, ["K01", "K02"]);
  assert.equal(document.dependency_edges_declared, true);
});

test("parses a block-style semantic-unit DAG", () => {
  const document = parseReasoningTreeDocument(BLOCK_TREE);
  assert.equal(document.format, REASONING_TREE_FORMAT.UNIT_DAG);
  assert.equal(document.units.length, 2);
  assert.deepEqual(document.units[1].depends_on, ["C01"]);
});

test("parses the historical JSON linear-path tree without inventing edges", () => {
  const document = parseReasoningTreeDocument(JSON_LINEAR_TREE);
  assert.equal(document.format, REASONING_TREE_FORMAT.JSON_LINEAR_PATH);
  assert.equal(document.units.length, 3);
  assert.equal(document.dependency_edges_declared, false);
  assert.ok(document.units.every((unit) => unit.depends_on.length === 0));
});

test("parses the historical categorized YAML tree", () => {
  const document = parseReasoningTreeDocument(CATEGORIZED_TREE);
  assert.equal(document.format, REASONING_TREE_FORMAT.CATEGORIZED_YAML);
  assert.equal(document.units.length, 4);
  assert.equal(document.dependency_edges_declared, false);
});

test("an unrecognised document yields unknown, never a depth of zero", () => {
  const document = parseReasoningTreeDocument("not a tree at all");
  assert.equal(document.format, REASONING_TREE_FORMAT.UNKNOWN);
  assert.equal(document.declared_unit_count, null);
  assert.deepEqual(document.units, []);
});

/* ------------------------------------------------------------------ structure */

test("audits a branched DAG: depth, joins, branching and auditability", () => {
  const audit = auditReasoningTree(parseReasoningTreeDocument(DAG_TREE));
  assert.equal(audit.parsed_unit_count, 5);
  assert.equal(audit.unit_count_agrees_with_declaration, true);
  assert.equal(audit.structure_class, "branched_dag");
  // K01/K02 are roots (1); K03 and K04 sit at 2; K05 joins them at 3.
  assert.equal(audit.longest_dependency_chain_nodes, 3);
  assert.equal(audit.multi_parent_nodes, 2);
  assert.equal(audit.peak_branching_factor, 2);
  assert.equal(audit.has_cycle, false);
  assert.deepEqual(audit.missing_dependencies, []);
  assert.equal(audit.structurally_auditable, true);
});

test("a chain with declared edges is classified as a linear chain, not a DAG", () => {
  const audit = auditReasoningTree(parseReasoningTreeDocument(BLOCK_TREE));
  assert.equal(audit.structure_class, "linear_chain");
  assert.equal(audit.longest_dependency_chain_nodes, 2);
  assert.equal(audit.multi_parent_nodes, 0);
});

test("a tree with no declared edges reports not_declared and null structural metrics", () => {
  const audit = auditReasoningTree(parseReasoningTreeDocument(JSON_LINEAR_TREE));
  assert.equal(audit.structure_class, "not_declared");
  assert.equal(audit.longest_dependency_chain_nodes, null);
  assert.equal(audit.multi_parent_nodes, null);
  assert.equal(audit.peak_branching_factor, null);
  assert.equal(audit.structurally_auditable, false, "a tree without edges cannot be structurally audited");
});

test("detects dangling dependencies and cycles", () => {
  const dangling = auditReasoningTree(
    parseReasoningTreeDocument(
      "level: L10\nunit_count: 1\nsemantic_units:\n  - {id: A, inference: \"x\", depends_on: [ZZ], evidence: [], role: \"\"}\n",
    ),
  );
  assert.deepEqual(dangling.missing_dependencies, [{ unit: "A", missing: "ZZ" }]);
  assert.equal(dangling.structurally_auditable, false);

  const cyclic = auditReasoningTree(
    parseReasoningTreeDocument(
      "level: L10\nunit_count: 2\nsemantic_units:\n  - {id: A, inference: \"x\", depends_on: [B], evidence: [], role: \"\"}\n  - {id: B, inference: \"y\", depends_on: [A], evidence: [], role: \"\"}\n",
    ),
  );
  assert.equal(cyclic.has_cycle, true);
  assert.equal(cyclic.structurally_auditable, false);
});

test("detects duplicate inferences, which cannot all be irreducible", () => {
  const audit = auditReasoningTree(
    parseReasoningTreeDocument(
      "level: L10\nunit_count: 2\nsemantic_units:\n  - {id: A, inference: \"The same fact.\", depends_on: [], evidence: [], role: \"\"}\n  - {id: B, inference: \"the  same fact.\", depends_on: [A], evidence: [], role: \"\"}\n",
    ),
  );
  assert.equal(audit.duplicate_inferences.length, 1);
});

test("detects a declared count that disagrees with the parsed unit count", () => {
  const audit = auditReasoningTree(parseReasoningTreeDocument(DAG_TREE.replace("unit_count: 5", "unit_count: 30")));
  assert.equal(audit.unit_count_agrees_with_declaration, false);
});

/* ------------------------------------------------------------ strict verdicts */

test("strict levels are lower bounds, not equalities", () => {
  assert.equal(STRICT_DEPTH_THRESHOLDS.L10, 10);
  assert.equal(STRICT_DEPTH_THRESHOLDS.L30, 30);
  assert.equal(strictDepthVerdict({ level: "L30", auditedSemanticDepth: 32 }).ok, true);
  assert.equal(strictDepthVerdict({ level: "L30", auditedSemanticDepth: 30 }).ok, true);
  assert.equal(strictDepthVerdict({ level: "L10", auditedSemanticDepth: 10 }).ok, true);
  assert.equal(strictDepthVerdict({ level: "L10", auditedSemanticDepth: 32 }).ok, true);
});

test("an audited depth below the bound fails, and an unaudited depth is never a pass", () => {
  const low = strictDepthVerdict({ level: "L30", auditedSemanticDepth: 29 });
  assert.equal(low.ok, false);
  assert.ok(low.reason.includes("below the strict L30 lower bound"));

  const missing = strictDepthVerdict({ level: "L30", auditedSemanticDepth: null });
  assert.equal(missing.ok, false);
  assert.ok(missing.reason.includes("No audited semantic depth"));

  assert.equal(strictDepthVerdict({ level: "L99", auditedSemanticDepth: 500 }).ok, false);
});

test("F-10: nominal L50 with audited depth 38 is not a genuine L50 condition", () => {
  const verdict = strictDepthVerdict({ level: "L50", auditedSemanticDepth: 38 });
  assert.equal(verdict.ok, false);
  assert.equal(verdict.threshold, 50);
});

/* ------------------------------------------------------------------- registry */

test("resolves nominal and audited depth without touching the manifest", () => {
  const manifest = { reasoning: { level: "L50", unit_count: 50 } };
  const registry = {
    schema_version: DEPTH_AUDIT_REGISTRY_SCHEMA_VERSION,
    entries: {
      "X-1-L50-001": {
        nominal_depth: "L50",
        nominal_unit_count: 50,
        audited_semantic_depth: 12,
        depth_audit_status: DEPTH_AUDIT_STATUS.STRICT_FAIL,
        depth_audit_method: DEPTH_AUDIT_METHOD.HUMAN_SHORTEST_PATH,
        depth_audit_report: "audit.md",
      },
    },
  };
  const resolved = resolveDepthAudit("X-1-L50-001", registry, manifest);
  assert.equal(resolved.nominal_depth, "L50");
  assert.equal(resolved.nominal_unit_count, 50);
  assert.equal(resolved.audited_semantic_depth, 12);
  assert.equal(resolved.strict_depth_ok, false);
  assert.deepEqual(manifest, { reasoning: { level: "L50", unit_count: 50 } }, "the manifest must not be mutated");
});

test("an unregistered variant is not_audited and strictly ineligible", () => {
  const resolved = resolveDepthAudit("UNKNOWN-1-L10-001", emptyDepthAuditRegistry(), {
    reasoning: { level: "L10", unit_count: 10 },
  });
  assert.equal(resolved.depth_audit_status, DEPTH_AUDIT_STATUS.NOT_AUDITED);
  assert.equal(resolved.audited_semantic_depth, null);
  assert.equal(resolved.strict_depth_ok, false);
});

test("strict eligibility rejects not_audited, nominal_only and strict_fail alike", () => {
  const registry = {
    schema_version: DEPTH_AUDIT_REGISTRY_SCHEMA_VERSION,
    entries: {
      NOMINAL: { nominal_depth: "L70", depth_audit_status: DEPTH_AUDIT_STATUS.NOMINAL_ONLY },
      FAILING: { nominal_depth: "L30", audited_semantic_depth: 9, depth_audit_status: DEPTH_AUDIT_STATUS.STRICT_FAIL },
      PASSING: { nominal_depth: "L30", audited_semantic_depth: 30, depth_audit_status: DEPTH_AUDIT_STATUS.STRICT_PASS },
    },
  };
  assert.equal(strictDepthEligibility("NOMINAL", registry).ok, false);
  assert.equal(strictDepthEligibility("FAILING", registry).ok, false);
  assert.equal(strictDepthEligibility("MISSING", registry).ok, false);
  assert.equal(strictDepthEligibility("PASSING", registry).ok, true);
});

test("a malformed or absent registry file degrades to empty, never to a pass", async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "d4j-depth-registry-"));
  try {
    assert.deepEqual(await loadDepthAuditRegistry(path.join(dir, "missing.json")), emptyDepthAuditRegistry());
    const badPath = path.join(dir, "bad.json");
    await fs.writeFile(badPath, "{ not json");
    assert.deepEqual(await loadDepthAuditRegistry(badPath), emptyDepthAuditRegistry());
    const wrongSchema = path.join(dir, "wrong.json");
    await fs.writeFile(wrongSchema, JSON.stringify({ schema_version: "other", entries: { A: {} } }));
    assert.deepEqual(await loadDepthAuditRegistry(wrongSchema), emptyDepthAuditRegistry());
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
});

/* -------------------------------------------------- the repository's own state */

test("the committed depth-audit registry admits exactly the three strict artifacts", async () => {
  const registryPath = path.join(
    process.cwd(),
    "..",
    "..",
    "benchmark_runs",
    "analysis",
    "research-validity",
    "depth-audit-registry.json",
  );
  const registry = await loadDepthAuditRegistry(registryPath);
  if (!Object.keys(registry.entries).length) return; // registry not present in this checkout

  const passing = Object.values(registry.entries)
    .filter((entry) => entry.depth_audit_status === DEPTH_AUDIT_STATUS.STRICT_PASS)
    .map((entry) => entry.variant_id)
    .sort();
  assert.deepEqual(passing, ["CHART-1-L10-STRICT-001", "CHART-1-L30-DEPENDENCY-001", "CLOSURE-1-L30-STRICT-001"]);

  // F-5: the old Closure L10 must not be usable as a strict L10 arm.
  assert.equal(strictDepthEligibility("CLOSURE-1-L10-001", registry).ok, false);
  // F-10: no nominal L50/L70 artifact may enter a strict cohort.
  for (const entry of Object.values(registry.entries)) {
    if (entry.nominal_depth === "L50" || entry.nominal_depth === "L70") {
      assert.equal(strictDepthEligibility(entry.variant_id, registry).ok, false, `${entry.variant_id} must be strictly ineligible`);
    }
  }
});
