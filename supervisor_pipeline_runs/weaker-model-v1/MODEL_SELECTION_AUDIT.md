# Model selection audit (weaker-model-v1)

Written on 2026-10-12, before any paid call in this root.

**Goal.** Find an OpenAI model weaker than GPT-5.6 that can still operate the frozen mini-swe-agent protocol. It must use the
bash and submit tools, read code, run tests, and submit a ranked list of ten.

## Sources

- **Availability.** `GET /v1/models` with the authorised OpenAI key. The key was loaded in-process and never printed. 141 model
  ids were visible on 2026-10-12, and the chat-capable ones are listed below. A bare `gpt-5.6` id is not listed, but it is the
  id every GPT-5.6 run in mechanism-search-v1 used successfully, and responses reported `gpt-5.6`.
- **Capabilities.** The litellm 1.98.0 model map, which ships with the installed harness. It gives the context window, function
  calling, reasoning support and list price.
- **Harness compatibility.**
  - mini-swe-agent 2.4.6 sends `openai/<id>` through litellm with the bash and submit tools as function tools.
  - The run config always carries `model_kwargs: {drop_params: true, reasoning_effort: medium}`. litellm drops parameters a model
    does not support, so the identical config is valid for both reasoning and non-reasoning models.
  - litellm routes models with function tools and active reasoning (the GPT-5.x line) through the Responses API bridge, and the
    others through Chat Completions. Both paths are inside the harness.
  - Compatibility is confirmed behaviourally by the smoke run and by each server's health probes before its runs.
- **Expected cost per run.** The GPT-5.6 held-out runs used a median of 54,234 input and 3,150 output tokens. Pricing those at
  each model's list price, scaled by GPT-5.6's observed ratio of actual to list-price cost (0.60, which reflects prompt caching),
  gives the estimate below. Weaker models may take more or fewer steps.

## Candidates

| Model id (alias → snapshot) | Family | Context (in/out) | Function calling | Reasoning control | List $/M (in/out) | Est. per run | Est. 27 runs |
|---|---|---|---|---|---|---|---|
| gpt-5.6 (reference, not re-run) | GPT-5.x flagship | 922k / 128k | yes | effort medium | 4.0 / 20.0 | $0.17 (observed) | — |
| **gpt-5.5** → gpt-5.5-2026-04-23 | GPT-5.x flagship, one generation back | 1.05M / 128k | yes | effort medium | 5.0 / 30.0 | $0.22 | $5.9 |
| gpt-5.4 → gpt-5.4-2026-03-05 | GPT-5.x flagship | 1.05M / 128k | yes | effort medium | 2.5 / 15.0 | $0.11 | $3.0 |
| **gpt-5** → gpt-5-2025-08-07 | first GPT-5 flagship | 272k / 128k | yes | effort medium | 1.25 / 10.0 | $0.06 | $1.6 |
| gpt-5.4-mini → gpt-5.4-mini-2026-03-17 | small reasoning | 272k / 128k | yes | effort medium | 0.75 / 4.5 | $0.03 | $0.9 |
| **gpt-5-mini** → gpt-5-mini-2025-08-07 | small reasoning | 272k / 128k | yes | effort medium | 0.25 / 2.0 | $0.012 | $0.3 |
| gpt-5.4-nano → gpt-5.4-nano-2026-03-17 | smallest reasoning | 272k / 128k | yes | effort medium | 0.20 / 1.25 | $0.009 | $0.2 |
| **gpt-5-nano** → gpt-5-nano-2025-08-07 | smallest reasoning | 272k / 128k | yes | effort medium | 0.05 / 0.40 | $0.002 | $0.06 |
| **gpt-4.1-mini** → gpt-4.1-mini-2025-04-14 | small non-reasoning | 1.05M / 33k | yes | none (dropped) | 0.40 / 1.6 | $0.016 | $0.4 |
| **gpt-4o-mini** → gpt-4o-mini-2024-07-18 | small non-reasoning | 128k / 16k | yes | none (dropped) | 0.15 / 0.6 | $0.006 | $0.2 |

**Considered and not used:**

- gpt-5.2 and gpt-5.1 are flagships between 5.4 and 5. gpt-5.4 already sits between the ladder's first two rungs as the
  intermediate.
- o4-mini, o3, gpt-4.1 and gpt-4o are other model lines, not needed for a monotone ladder.
- The `-pro`, `-codex`, `-chat-latest` and `gpt-5.6-*` / `gpt-6*` variants are other products or not clearly weaker.
- gpt-4.1-nano was not taken, because it is the next step below gpt-4.1-mini only if needed.
- gpt-3.5-turbo is excluded: its 16k context is smaller than a typical trajectory (GPT-5.6 median input 54k tokens).

## Ladder (preregistered in PREREGISTRATION.md)

The primary rungs run from strongest to weakest:

**L1** gpt-5.5 → **L2** gpt-5 → **L3** gpt-5-mini → **L4** gpt-5-nano → **L5** gpt-4.1-mini → **L6** gpt-4o-mini.

**Intermediates**, used only if a primary rung is operationally too weak right after a viable but too-accurate rung:

- gpt-5.4 between L1 and L2;
- gpt-5.4-mini between L2 and L3;
- gpt-5.4-nano between L3 and L4.

**Rationale.**

- L1 is the closest weaker model, as the brief requires.
- Each later primary rung is a clear capability step: an older flagship, then smaller reasoning models, then non-reasoning
  models.
- The intermediates guard against overshooting from a model at ceiling into operational collapse.
- The ordering beyond the GPT-5 line is an expectation, not a verified ranking. The procedure does not depend on its accuracy,
  because each rung is measured.
