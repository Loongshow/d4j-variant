# AGENTS.md

## Research Objective

This repository supports a thesis project on generating semantic bug variants
from real Defects4J bugs and human-authored reasoning trees.

A generated variant must preserve a meaningful part of the original bug's
reasoning structure while changing at least one of:

1. fault location,
2. trigger condition,
3. propagation path,
4. observable failure mode,
5. affected API path.

The current phase only targets L10 and L30 variants.

## Depth Levels

Use auditable reasoning units, not arbitrary chain-of-thought sentence counts.

Reasoning units include:

- failing assertion or exception,
- input constraint,
- environment, runtime, or configuration condition,
- relevant public API call,
- internal branch decision,
- helper method result,
- state mutation,
- cross-method propagation,
- cross-file propagation,
- observable failure.

### L10 Variant

- Target 8-15 reasoning units.
- Prefer one file or one direct helper call.
- Prefer one localized production-code fault.
- Require one deterministic new triggering test.
- Use this level first to smoke-test the pipeline.

### L30 Variant

- Target 20-35 reasoning units.
- Require a longer path than L10, such as helper propagation, cross-file API
  path, state/config interaction, or indirect observable failure.
- Still prefer one localized production-code fault.
- Require one or two deterministic new triggering tests.

## General Rules

- Start variants from the fixed Defects4J revision, not the original buggy
  revision.
- Do not edit production code before analysis and candidate review are complete.
- Do not modify developer tests merely to make validation pass.
- Do not generate compilation errors as bug variants.
- Do not introduce random syntactic mutations without semantic justification.
- Do not copy the original buggy patch into another file mechanically.
- Do not add unrelated refactoring, formatting changes, or dependencies.
- Prefer one localized production-code fault.
- Preserve the project's existing coding style.
- Every factual claim about the bug must be supported by source code, test
  output, or the buggy/fixed diff.
- Clearly distinguish observations from hypotheses.

## Variant Validity Criteria

A valid variant must satisfy all of the following:

1. The clean fixed baseline compiles.
2. Existing developer tests pass on the clean fixed baseline, or any pre-existing
   failures are documented before variant work begins.
3. The new triggering test passes on the clean fixed baseline.
4. The variant compiles.
5. At least one new triggering test fails on the variant.
6. The same new triggering test passes on the clean fixed baseline.
7. The failure is deterministic across at least three runs.
8. The fault is in production code.
9. The patch is minimal and localized.
10. The variant is not equivalent to the original Defects4J bug.
11. The variant has a documented reasoning tree and generation rationale.

## Required Workflow

Always separate these phases:

1. original bug analysis,
2. candidate generation,
3. candidate review,
4. implementation,
5. validation,
6. packaging.

During analysis, candidate generation, and candidate review, do not edit
production code unless explicitly instructed.

## Agent Roles

Use these roles either as separate Codex threads/subagents or as sequential
prompts in one thread.

### Agent 1: Original Bug Analyst

Goal: reconstruct the original bug using evidence.

Output:

- failing test summary,
- modified production classes,
- buggy method/location,
- buggy/fixed diff explanation,
- canonical reasoning tree using R/C/D/S/F/O/P,
- reasoning unit count,
- reusable reasoning-tree nodes for L10/L30 variants.

### Agent 2: Variant Designer

Goal: propose candidate semantic variants without editing files.

Output for each candidate:

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

### Agent 3: Benchmark Reviewer

Goal: reject weak or invalid candidates before implementation.

Reject candidates that are:

- equivalent to the original bug,
- too trivial for the claimed level,
- too artificial,
- flaky,
- broad refactors,
- syntax-only mutations,
- not testable by deterministic triggering tests.

### Agent 4: Implementer and Validator

Goal: implement one approved variant and package the result.

Rules:

- inspect source and tests before editing,
- modify production code only for the injected bug,
- add only the tests needed to expose the variant,
- keep the patch minimal,
- run validation commands and report outputs.

## Required Variant Report

For every packaged variant, include:

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
- difference from the original bug,
- limitations and possible equivalent behaviour,
- validation commands and results.

## First Recommended Experiment

Use Chart-1 as the first L10 experiment.

Suggested target:

- preserve the legend/item semantic expectation,
- avoid mechanically recreating the original inverted dataset-null condition,
- prefer a nearby but distinct trigger, branch, or API path,
- add a small deterministic JUnit test that passes on the fixed baseline and
  fails only after the injected production-code fault.
