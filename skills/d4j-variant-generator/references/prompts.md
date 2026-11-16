# Prompt Library

Use these prompts as role templates. Replace bracketed fields before use.

## Agent 1: Original Bug Analyst

```text
Use $d4j-variant-generator.

Analyze the original Defects4J bug [PROJECT]-[BUG_ID] for benchmark variant
generation.

Do not edit files.

Tasks:
1. Inspect the relevant source, tests, Defects4J metadata, and buggy/fixed diff.
2. Identify the original failing test.
3. Identify modified production classes.
4. Explain the original semantic root cause.
5. Build a reasoning tree using R/C/D/S/F/O/P.
6. Count auditable reasoning units.
7. Identify which reasoning-tree nodes are reusable for L10/L30 variants.

Output only a structured analysis report.
```

## Agent 2: Variant Designer

```text
Use $d4j-variant-generator.

Generate candidate semantic bug variants from the original reasoning tree for
[PROJECT]-[BUG_ID].

Target levels:
- one L10 candidate
- one L30 candidate

Rules:
- Do not edit files.
- Do not propose syntax-only mutations.
- Do not copy the original bug mechanically.
- Preserve a meaningful part of the original reasoning structure.
- Change at least one of: fault-site relocation, trigger-condition
  substitution, propagation-path modification, failure-mode modification, or
  API-path substitution.
- Each candidate must be testable with a deterministic new triggering test.

For each candidate, provide:
1. Variant ID.
2. Target level.
3. Changed reasoning-tree node.
4. Preserved reasoning-tree nodes.
5. Proposed production-code fault.
6. Proposed new triggering test.
7. Expected failure symptom.
8. Why it is not equivalent to the original bug.
9. Estimated reasoning unit count.
10. Risk assessment.
```

## Agent 3: Benchmark Reviewer

```text
Use $d4j-variant-generator.

Act as a strict benchmark validity reviewer for the proposed variants of
[PROJECT]-[BUG_ID].

Reject or revise candidates that:
- are equivalent to the original bug,
- are too trivial for the claimed level,
- are too artificial,
- depend on flaky behavior,
- require broad refactoring,
- only mutate syntax,
- do not require the claimed reasoning depth,
- cannot be validated by deterministic tests.

For each candidate:
1. Accept / reject / revise.
2. Validity risk.
3. Whether the L10/L30 label is credible.
4. Required evidence before implementation.
5. Final recommended variant to implement first.
```

## Agent 4: Implementer And Validator

```text
Use $d4j-variant-generator.

Implement the approved [L10/L30] semantic bug variant for [PROJECT]-[BUG_ID].

Rules:
- Start from the fixed baseline.
- Inspect source and tests before editing.
- Modify production code only for the injected bug.
- Add only the tests needed to expose the variant.
- Keep the production-code patch minimal.
- Preserve project style.
- Do not touch unrelated files.

After editing:
1. Run compile.
2. Run the new triggering test.
3. Run relevant existing tests if feasible.
4. Run the failing test three times on the variant.
5. Report whether the test passes on baseline and fails on variant.
6. Create the final variant report.
```
