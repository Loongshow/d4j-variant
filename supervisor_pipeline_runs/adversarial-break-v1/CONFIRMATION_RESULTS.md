# Confirmation results (all models, all runs to date)

Protocol v2 (frozen prompt, 50 tool calls, 5 test runs, 300 s, structured submission) with one deviation from the GPT-5.6 runs: `defects4j test` could not execute for the Claude agents (`diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`). Provider errors and provider stalls are excluded from every denominator (`diagnostic/PROVIDER_STALL_RULE.md`).

| Attack | Model | answered / attempted | Acc@1 (answered) | Acc@1 (all attempts) | label (all) | no-answer (budget/time) | provider errors | MRR | gold ranks | gold discovered | gold in top-10 | tool calls | first gold | rank-1 roles | failure taxonomy | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `BASE-LONG` | claude-haiku-4-5 | 1/3 | 1.0 | **0.333** | STRONG | 2 | 0 | 1.0 | [1] | 1/1 | 1/1 | 49 | 21 | {"gold": 1} | {} | 0.5205 |
| `BASE-LONG` | claude-sonnet-4-6 | 7/13 | 1.0 | **0.875** | WEAK | 1 | 5 | 1.0 | [1, 1, 1, 1, 1, 1, 1] | 7/7 | 7/7 | 39 | 16 | {"gold": 7} | {} | 3.5561 |
| `CMB-01` | claude-haiku-4-5 | 0/3 | - | **0.0** | VERY STRONG | 3 | 0 | - | [] | - | - | - | - | - | - | 0.5735 |
| `CMB-01` | claude-sonnet-4-6 | 7/11 | 0.0 | **0.0** | VERY STRONG | 3 | 1 | 0.2 | [5, 5, 5, 5, 5, 5, 5] | 7/7 | 7/7 | 44 | 13.6 | {"producer": 7} | {"OWNERSHIP_MISATTRIBUTION": 7} | 4.4184 |
| `CMB-01` | claude-opus-5-5 | 5/5 | 0.0 | **0.0** | VERY STRONG | 0 | 0 | 0.433 | [2, 3, 2, 2, 3] | 5/5 | 5/5 | 6.2 | 4.8 | {"producer": 5} | {"OWNERSHIP_MISATTRIBUTION": 5} | 0.4675 |
| `CTX-01` | claude-haiku-4-5 | 1/3 | 0.0 | **0.0** | VERY STRONG | 2 | 0 | 0.25 | [4] | 1/1 | 1/1 | 48 | 10 | {"deeper-stage": 1} | {"DEPTH_PRIOR": 1} | 0.5126 |
| `CTX-01` | claude-sonnet-4-6 | 8/16 | 0.0 | **0.0** | VERY STRONG | 2 | 6 | 0.25 | [4, 4, 4, 4, 4, 4, 4, 4] | 8/8 | 8/8 | 43.4 | 7.9 | {"deeper-stage": 8} | {"DEPTH_PRIOR": 8} | 5.0755 |
| `CTX-01` | claude-opus-5-5 | 5/5 | 0.4 | **0.4** | STRONG | 0 | 0 | 0.567 | [1, 4, 1, 3, 4] | 5/5 | 5/5 | 6.8 | 3 | {"gold": 2, "deeper-stage": 3} | {"DEPTH_PRIOR": 3} | 0.4785 |
| `DEP-01` | claude-haiku-4-5 | 1/3 | 1.0 | **0.333** | STRONG | 2 | 0 | 1.0 | [1] | 1/1 | 1/1 | 47 | 10 | {"gold": 1} | {} | 0.6578 |
| `DEP-01` | claude-sonnet-4-6 | 1/3 | 1.0 | **1.0** | NULL | 0 | 2 | 1.0 | [1] | 1/1 | 1/1 | 31 | 11 | {"gold": 1} | {} | 1.041 |
| `LEX-01` | claude-haiku-4-5 | 1/3 | 1.0 | **0.333** | STRONG | 2 | 0 | 1.0 | [1] | 1/1 | 1/1 | 42 | 25 | {"gold": 1} | {} | 0.6376 |
| `LEX-01` | claude-sonnet-4-6 | 9/14 | 0.889 | **0.889** | WEAK | 0 | 5 | 0.944 | [2, 1, 1, 1, 1, 1, 1, 1, 1] | 9/9 | 9/9 | 36.1 | 16.7 | {"decoy-lexical": 1, "gold": 8} | {"LEXICAL_MISATTRIBUTION": 1} | 3.8695 |
| `LEX-01` | claude-opus-5-5 | 5/5 | 1.0 | **1.0** | NULL | 0 | 0 | 1.0 | [1, 1, 1, 1, 1] | 5/5 | 5/5 | 6.8 | 6 | {"gold": 5} | {} | 0.5207 |
| `MAX-01` | claude-sonnet-4-6 | 5/10 | 0.0 | **0.0** | VERY STRONG | 5 | 0 | 0.2 | [5, 5, 5, 5, 5] | 5/5 | 5/5 | 45 | 14.8 | {"producer": 5} | {"OWNERSHIP_MISATTRIBUTION": 5} | 4.6071 |
| `MAX-01` | claude-opus-5-5 | 5/6 | 0.2 | **0.2** | VERY STRONG | 0 | 1 | 0.467 | [1, 3, 3, 3, 3] | 5/5 | 5/5 | 7.4 | 4.6 | {"gold": 1, "producer": 4} | {"OWNERSHIP_MISATTRIBUTION": 4} | 0.5748 |
| `NAV-01` | claude-haiku-4-5 | 2/3 | 1.0 | **0.667** | MODERATE | 1 | 0 | 1.0 | [1, 1] | 2/2 | 2/2 | 34.5 | 12 | {"gold": 2} | {} | 0.6304 |
| `NAV-01` | claude-sonnet-4-6 | 3/3 | 1.0 | **1.0** | NULL | 0 | 0 | 1.0 | [1, 1, 1] | 3/3 | 3/3 | 28 | 8.3 | {"gold": 3} | {} | 0.7499 |
| `OVL-01` | claude-haiku-4-5 | 2/3 | 1.0 | **0.667** | MODERATE | 1 | 0 | 1.0 | [1, 1] | 2/2 | 2/2 | 44 | 9 | {"gold": 2} | {} | 0.599 |
| `OVL-01` | claude-sonnet-4-6 | 3/3 | 1.0 | **1.0** | NULL | 0 | 0 | 1.0 | [1, 1, 1] | 3/3 | 3/3 | 23.3 | 6 | {"gold": 3} | {} | 1.3052 |
| `OWN-01` | claude-haiku-4-5 | 2/3 | 1.0 | **0.667** | MODERATE | 1 | 0 | 1.0 | [1, 1] | 2/2 | 2/2 | 39.5 | 6 | {"gold": 2} | {} | 0.5211 |
| `OWN-01` | claude-sonnet-4-6 | 3/3 | 1.0 | **1.0** | NULL | 0 | 0 | 1.0 | [1, 1, 1] | 3/3 | 3/3 | 20.7 | 3.3 | {"gold": 3} | {} | 0.5551 |

## Reading

**Opus (n=5 per attack, all runs answered, no exhaustion).**
- `ADV-DEFINER-01` (CMB-01): Acc@1 0.0, gold ranks 2, 3, 2, 2, 3, MRR 0.43, six to eight tool calls, failing test never run. Every
  run ranked the definer `PlotUtilities.drift` first with the same argument ("the drift direction is reversed"). VERY STRONG.
- `ADV-MASK-01` (CTX-01): Acc@1 0.4, ranks 1, 4, 1, 3, 4, MRR 0.60. The misses rank the chain in strict depth order with the deepest
  hop `overlay` first; the hits cite the second consumer `BitField.setValue`. STRONG.
- `ADV-LEX-01` (LEX-01): Acc@1 1.0, five of five, MRR 1.0. The decoy `wordOffset` is second in every ranking. NULL.

**Sonnet (n=10 per attack).**
- `ADV-DEFINER-01`: Acc@1 0.0 over all attempts and over answered runs. Ten valid attempts after one top-up: seven answered runs, gold
  rank 5 in each, `drift` first in each; one timeout with the agent still working at the deadline and two budget exhaustions; one hung
  request excluded. 37 to 51 tool calls per answered
  run, failing test run once. VERY STRONG.
- `ADV-MASK-01`: no hit in ten valid attempts (sixteen launched; six hung requests excluded). All eight answered runs ranked
  `overlay, combine, widen, compose`: deepest hop first, gold fourth, the same depth-ordered miss as Opus's misses; two runs exhausted
  the budget without a valid submission. VERY STRONG.
- `ADV-LEX-01`: the screening signal did not hold. Nine answered runs (fourteen launched, five hung requests excluded), eight with the
  gold first and one with the decoy first (gold second). Acc@1 0.89, MRR 0.94: WEAK. With Opus at 5 of 5 the witness
  inversion is close to null on both models once the sample is large enough.
- Control (`BASE-LONG`, plain `CONVERSION-LONG-TREATMENT-01`, ten runs): seven of eight valid attempts answered with the gold first (Acc@1 over valid attempts 0.875), one budget exhaustion without a valid submission, five hung requests excluded (thirteen launched). Sonnet's no-answer rate without an attack is therefore about one in eight valid attempts, against three in ten on `ADV-DEFINER-01`, two in ten on `ADV-MASK-01` and five in ten on the composite.

**Denominators.** "answered / attempted" excludes the one provider stall (`opus55 / ADV-COMPOSITE-01 / run-002`, replaced by a
sixth run) and nothing else; no `provider_error` occurred. Acc@1 over all attempts treats every timeout with steady work and every
budget exhaustion as a miss; the control block (`BASE-LONG`, ten Sonnet runs, three Haiku runs of the plain
`CONVERSION-LONG-TREATMENT-01` variant) gives the exhaustion rate without an attack.
