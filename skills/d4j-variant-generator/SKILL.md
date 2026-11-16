---
name: d4j-variant-generator
description: Generate, review, implement, validate, and package semantic bug variants derived from Defects4J bugs for thesis benchmarking. Use when working on Defects4J bug variants, L10/L30 reasoning-depth variants, test-to-bug localization benchmark data, reasoning-tree annotations, or agent workflows for creating validated Java bug variants.
---

# D4J Variant Generator

## Purpose

Use this skill to create benchmark-grade semantic bug variants from real
Defects4J bugs. The goal is not to create arbitrary broken code; the goal is to
preserve part of an original bug's reasoning structure while changing a
controlled semantic dimension and validating the result with deterministic
tests.

## Required Mindset

Treat every variant as a benchmark artifact. Prefer evidence, minimal edits,
and reproducibility over creative mutation.

Separate observations from hypotheses. Support factual claims with source code,
test output, metadata from Defects4J, or the original buggy/fixed diff.

## Depth Levels

Count auditable reasoning units, not chain-of-thought sentences.

Reasoning units include failing assertions, exceptions, input constraints,
runtime/config conditions, public API calls, branch decisions, helper results,
state mutations, cross-method propagation, cross-file propagation, and
observable failures.

### L10

- Target 8-15 reasoning units.
- Prefer a single file or one direct helper call.
- Prefer one localized production-code fault.
- Add one deterministic triggering test.
- Use L10 first to validate the workflow.

### L30

- Target 20-35 reasoning units.
- Require a longer path than L10: helper propagation, cross-file API path,
  state/config interaction, or indirect observable failure.
- Still prefer one localized production-code fault.
- Add one or two deterministic triggering tests.

## Workflow

Always perform these phases in order.

1. Analyze the original bug.
2. Generate candidate variants without editing files.
3. Review candidates strictly.
4. Implement one approved candidate.
5. Validate the variant.
6. Package the report.

During phases 1-3, do not edit production code.

## Phase 1: Original Bug Analysis

Inspect the relevant source, tests, Defects4J metadata, and buggy/fixed diff.

Produce:

- failing test summary,
- modified production classes,
- buggy method/location,
- minimal buggy/fixed diff explanation,
- canonical reasoning tree using R/C/D/S/F/O/P,
- reasoning unit count,
- reusable reasoning-tree nodes for L10/L30 variants.

Reasoning tree schema:

- R: root semantic property
- C: trigger conditions
- D: intended decision
- S: intermediate state transition
- F: fault mechanism
- O: observable failure
- P: original patch strategy

## Phase 2: Candidate Generation

Generate multiple candidates before editing.

Each candidate must change at least one dimension:

- fault-site relocation,
- trigger-condition substitution,
- propagation-path modification,
- failure-mode modification,
- API-path substitution.

For each candidate, provide:

- variant ID,
- target level,
- changed reasoning-tree node,
- preserved reasoning-tree nodes,
- proposed production-code fault,
- proposed new triggering test,
- expected failure symptom,
- reason it is not equivalent to the original bug,
- estimated reasoning unit count,
- risk assessment.

## Phase 3: Candidate Review

Reject candidates that are equivalent to the original bug, too trivial for the
claimed depth, too artificial, flaky, syntax-only, broad refactors, or not
testable with deterministic triggering tests.

Choose one final candidate to implement. If none are good enough, return to
candidate generation.

## Phase 4: Implementation

Start from the fixed Defects4J baseline, not the original buggy version.

Rules:

- inspect source and tests before editing,
- confirm the clean baseline compiles where feasible,
- modify production code only for the injected bug,
- add or edit only the tests needed to expose the variant,
- keep production edits minimal and localized,
- preserve project style,
- avoid unrelated formatting changes.

## Phase 5: Validation

A valid variant must satisfy:

1. clean fixed baseline compiles,
2. existing developer tests pass on the clean fixed baseline, or known existing
   failures are documented before variant work begins,
3. new triggering test passes on the clean fixed baseline,
4. variant compiles,
5. new triggering test fails on the variant,
6. the failure is deterministic across at least three runs,
7. fault is in production code,
8. patch is minimal and localized,
9. variant is not equivalent to the original Defects4J bug,
10. variant has a documented reasoning tree and rationale.

## Phase 6: Packaging

Create a report containing:

- variant ID,
- original Defects4J project and bug ID,
- fixed baseline revision,
- depth level,
- reasoning unit count,
- original reasoning tree,
- variant reasoning tree,
- changed reasoning-tree node,
- source files modified,
- tests added,
- failing output,
- passing output,
- semantic root cause,
- difference from original bug,
- limitations and possible equivalent behaviour,
- validation commands and results.

## Prompt Library

For reusable role prompts, read `references/prompts.md`.
