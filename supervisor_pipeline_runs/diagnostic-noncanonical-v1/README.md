# diagnostic-noncanonical-v1 — DIAGNOSTIC / NON-CANONICAL / LEAKAGE-EXPOSED

Isolated experiment root for the 10-run GPT-5.6 diagnostic on the supervisor-generated pilot pair.
Nothing here is part of the canonical CRFLB corpus or its benchmark_runs. Layout:

- `variant-lab/server/`   frozen COPY of <repo>/variant-lab/server at build time (hash in EXPERIMENT_MANIFEST.json);
                          `node_modules` is a symlink. The server derives repoRoot from its own location, so
                          it uses THIS root's new_bug_variants/ and benchmark_runs/.
- `workspaces -> <repo>/workspaces`, `framework -> <repo>/framework`   read-only inputs (Lang-1 fixed checkout, defects4j).
- `new_bug_variants/Lang/bug-1/L20/<ID>/`   byte-identical copies of the two pilot packages + NON_CANONICAL_PILOT.md.
- `benchmark_runs/`   where the 10 runs land: benchmark_runs/mini-swe-agent-openai-gpt-5-6/<ID>/run-00N/
- `runs/`   empty (server expects it).

Purpose: NOT to estimate a causal effect of reasoning depth. Preregistered expectation: both arms may remain
at ceiling because the task exposes strong lexical/local evidence (see ../analysis/PILOT_LEAKAGE_AUDIT.md).
