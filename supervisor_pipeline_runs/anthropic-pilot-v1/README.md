# anthropic-pilot-v1

Anthropic support was added to the Defects4J fault-localization benchmark harness, verified against the
frozen GPT-5.6 protocol, and exercised in a small Claude pilot on frozen benchmark instances.

| | |
|---|---|
| Claude model | `claude-opus-5-5` via `anthropic/claude-opus-5-5` |
| Adapter change | 4 edits in 2 files, applied to an **isolated copy** of the harness; the frozen tree is byte-identical |
| OpenAI regression | both trees: 198 tests, 197 pass, 1 pre-existing fail, identical per-test outcomes |
| Protocol comparability | **NEAR_EQUIVALENT** (same prompt hash, tools, budget, timeouts, parser, scoring) |
| Pilot | 24/24 runs completed, 2.2794 USD |
| GPT-5.6 | not rerun; re-measured from frozen artifacts with the same script |

## Headline comparison

| Unit | Arm | Claude ranks | Claude tool calls | Claude first gold | GPT-5.6 ranks | GPT-5.6 tool calls | GPT-5.6 first gold |
|---|---|---|---|---|---|---|---|
| `CONVERSION-LONG-01` | CONTROL | [1, 1, 1] | 2 | 1 | [1, 1, 1, 1, 1] | 9.8 | 1.4 |
| `CONVERSION-LONG-01` | TREATMENT | [1, 1, 1] | 7.33 | 7 | [1, 1, 1, 1, 1] | 29.2 | 23.4 |
| `CHART-PIE-03` | CONTROL | [1, 1, 1] | 1.67 | 1 | [1, 1, 1, 1, 1] | 12.8 | 1.4 |
| `CHART-PIE-03` | TREATMENT | [3, 6, 6] | 7.33 | 6.33 | [6, 6, 6, 6, 6] | 21.6 | 17.6 |
| `CMP-LAYOUT-02` | CONTROL | [1, 1, 1] | 5 | 2 | [1, 1, 1, 1, 1] | 12.4 | 4.2 |
| `CMP-LAYOUT-02` | TREATMENT | [1, 1, 1] | 7 | 7 | [1, 1, 1, 3, 1] | 23.4 | 20.8 |
| `LANG-CONV-CAMO` | LOW | [1, 1, 1] | 6 | 6 | [1] | 30 | 26 |
| `LANG-CONV-CAMO` | HIGH | [1, 1, 1] | 7 | 6.67 | [] | - | - |

## Read in this order

1. `ANTHROPIC_ADAPTER_AUDIT.md` - what blocked Anthropic, the four edits, and how non-interference was proven.
2. `ANTHROPIC_MODEL_SELECTION.md` - the 12 models the credential can reach and why `claude-opus-5-5` was frozen.
3. `PROTOCOL_COMPARABILITY.md` - item-by-item protocol comparison and the five residual differences.
4. `SMOKE_TEST.md` - three probes plus one non-panel run, with every Phase 5 check.
5. `CLAUDE_PILOT_RESULTS.md` / `claude_pilot_results.json` - the pilot itself.
6. `GPT56_VS_CLAUDE.md`, `CAMOUFLAGE_CROSS_MODEL.md`, `OWNERSHIP_CROSS_MODEL.md`, `DEPTH_PRIOR_CROSS_MODEL.md`.
7. `CLAUDE_TRAJECTORY_AUDIT.md` - what Claude actually ran, command by command.
8. `INFRASTRUCTURE_ACCOUNTING.md`, `COST_ACCOUNTING.md`, `NEXT_ANTHROPIC_DECISION.md`.

## Isolation

`repoRoot` resolves to this directory, so Claude runs write only here. Variant packages are reached
read-only through a symlink to the frozen root, so both models score byte-identical artifacts. The pilot
server holds no OpenAI credential and cannot execute an OpenAI run. One incident is recorded in
`diagnostic/INCIDENT_frozen_server_process.md`: an over-broad process-kill pattern stopped the user's frozen
GPT-5.6 server process, which the user must restart; no artifact was affected and all three protected trees
verify unchanged.
