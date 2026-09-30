# Screening results (weaker Claude, 3 runs per attack)

Protocol v2 (frozen prompt, 50 tool calls, 5 test runs, 300 s, structured submission) with one deviation from the GPT-5.6 runs: `defects4j test` could not execute for the Claude agents (`diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`). Provider errors and provider stalls are excluded from every denominator (`diagnostic/PROVIDER_STALL_RULE.md`).

| Attack | Model | answered / attempted | Acc@1 (answered) | Acc@1 (all attempts) | label (all) | no-answer (budget/time) | provider errors | MRR | gold ranks | gold discovered | gold in top-10 | tool calls | first gold | rank-1 roles | failure taxonomy | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `BASE-LONG` | claude-sonnet-4-6 | 7/13 | 1.0 | **0.875** | WEAK | 1 | 5 | 1.0 | [1, 1, 1, 1, 1, 1, 1] | 7/7 | 7/7 | 39 | 16 | {"gold": 7} | {} | 3.5561 |
| `BASE-LONG` | claude-haiku-4-5 | 1/3 | 1.0 | **0.333** | STRONG | 2 | 0 | 1.0 | [1] | 1/1 | 1/1 | 49 | 21 | {"gold": 1} | {} | 0.5205 |
| `CMB-01` | claude-sonnet-4-6 | 7/11 | 0.0 | **0.0** | VERY STRONG | 3 | 1 | 0.2 | [5, 5, 5, 5, 5, 5, 5] | 7/7 | 7/7 | 44 | 13.6 | {"producer": 7} | {"OWNERSHIP_MISATTRIBUTION": 7} | 4.4184 |
| `CMB-01` | claude-haiku-4-5 | 0/3 | - | **0.0** | VERY STRONG | 3 | 0 | - | [] | - | - | - | - | - | - | 0.5735 |
| `CTX-01` | claude-sonnet-4-6 | 8/16 | 0.0 | **0.0** | VERY STRONG | 2 | 6 | 0.25 | [4, 4, 4, 4, 4, 4, 4, 4] | 8/8 | 8/8 | 43.4 | 7.9 | {"deeper-stage": 8} | {"DEPTH_PRIOR": 8} | 5.0755 |
| `CTX-01` | claude-haiku-4-5 | 1/3 | 0.0 | **0.0** | VERY STRONG | 2 | 0 | 0.25 | [4] | 1/1 | 1/1 | 48 | 10 | {"deeper-stage": 1} | {"DEPTH_PRIOR": 1} | 0.5126 |
| `DEP-01` | claude-sonnet-4-6 | 1/3 | 1.0 | **1.0** | NULL | 0 | 2 | 1.0 | [1] | 1/1 | 1/1 | 31 | 11 | {"gold": 1} | {} | 1.041 |
| `DEP-01` | claude-haiku-4-5 | 1/3 | 1.0 | **0.333** | STRONG | 2 | 0 | 1.0 | [1] | 1/1 | 1/1 | 47 | 10 | {"gold": 1} | {} | 0.6578 |
| `LEX-01` | claude-sonnet-4-6 | 9/14 | 0.889 | **0.889** | WEAK | 0 | 5 | 0.944 | [2, 1, 1, 1, 1, 1, 1, 1, 1] | 9/9 | 9/9 | 36.1 | 16.7 | {"decoy-lexical": 1, "gold": 8} | {"LEXICAL_MISATTRIBUTION": 1} | 3.8695 |
| `LEX-01` | claude-haiku-4-5 | 1/3 | 1.0 | **0.333** | STRONG | 2 | 0 | 1.0 | [1] | 1/1 | 1/1 | 42 | 25 | {"gold": 1} | {} | 0.6376 |
| `MAX-01` | claude-sonnet-4-6 | 5/10 | 0.0 | **0.0** | VERY STRONG | 5 | 0 | 0.2 | [5, 5, 5, 5, 5] | 5/5 | 5/5 | 45 | 14.8 | {"producer": 5} | {"OWNERSHIP_MISATTRIBUTION": 5} | 4.6071 |
| `NAV-01` | claude-sonnet-4-6 | 3/3 | 1.0 | **1.0** | NULL | 0 | 0 | 1.0 | [1, 1, 1] | 3/3 | 3/3 | 28 | 8.3 | {"gold": 3} | {} | 0.7499 |
| `NAV-01` | claude-haiku-4-5 | 2/3 | 1.0 | **0.667** | MODERATE | 1 | 0 | 1.0 | [1, 1] | 2/2 | 2/2 | 34.5 | 12 | {"gold": 2} | {} | 0.6304 |
| `OVL-01` | claude-sonnet-4-6 | 3/3 | 1.0 | **1.0** | NULL | 0 | 0 | 1.0 | [1, 1, 1] | 3/3 | 3/3 | 23.3 | 6 | {"gold": 3} | {} | 1.3052 |
| `OVL-01` | claude-haiku-4-5 | 2/3 | 1.0 | **0.667** | MODERATE | 1 | 0 | 1.0 | [1, 1] | 2/2 | 2/2 | 44 | 9 | {"gold": 2} | {} | 0.599 |
| `OWN-01` | claude-sonnet-4-6 | 3/3 | 1.0 | **1.0** | NULL | 0 | 0 | 1.0 | [1, 1, 1] | 3/3 | 3/3 | 20.7 | 3.3 | {"gold": 3} | {} | 0.5551 |
| `OWN-01` | claude-haiku-4-5 | 2/3 | 1.0 | **0.667** | MODERATE | 1 | 0 | 1.0 | [1, 1] | 2/2 | 2/2 | 39.5 | 6 | {"gold": 2} | {} | 0.5211 |

Ranking by observed Acc@1 on the primary weaker model (claude-sonnet-4-6), lowest first:

1. `CMB-01`: Acc@1 over all attempts 0.0 (VERY STRONG); over answered 0.0; no-answer 3/10; ranks [5, 5, 5, 5, 5, 5, 5]; haiku Acc@1(all) 0.0
2. `MAX-01`: Acc@1 over all attempts 0.0 (VERY STRONG); over answered 0.0; no-answer 5/10; ranks [5, 5, 5, 5, 5]
3. `CTX-01`: Acc@1 over all attempts 0.0 (VERY STRONG); over answered 0.0; no-answer 2/10; ranks [4, 4, 4, 4, 4, 4, 4, 4]; haiku Acc@1(all) 0.0
4. `BASE-LONG`: Acc@1 over all attempts 0.875 (WEAK); over answered 1.0; no-answer 1/8; ranks [1, 1, 1, 1, 1, 1, 1]; haiku Acc@1(all) 0.333
5. `LEX-01`: Acc@1 over all attempts 0.889 (WEAK); over answered 0.889; no-answer 0/9; ranks [2, 1, 1, 1, 1, 1, 1, 1, 1]; haiku Acc@1(all) 0.333
6. `DEP-01`: Acc@1 over all attempts 1.0 (NULL); over answered 1.0; no-answer 0/1; ranks [1]; haiku Acc@1(all) 0.333
7. `NAV-01`: Acc@1 over all attempts 1.0 (NULL); over answered 1.0; no-answer 0/3; ranks [1, 1, 1]; haiku Acc@1(all) 0.667
8. `OVL-01`: Acc@1 over all attempts 1.0 (NULL); over answered 1.0; no-answer 0/3; ranks [1, 1, 1]; haiku Acc@1(all) 0.667
9. `OWN-01`: Acc@1 over all attempts 1.0 (NULL); over answered 1.0; no-answer 0/3; ranks [1, 1, 1]; haiku Acc@1(all) 0.667

## Reading and advancement decision

Screening ran the five mandated designs (`ADV-DEPTH-01`, `ADV-REGISTRY-01`, `ADV-LEX-01`, `ADV-OVERLOAD-01`, `ADV-OWNER-01`) three
times each on claude-sonnet-4-6 (primary weaker model) and claude-haiku-4-5 (much weaker), then the two critic-top designs
built afterwards (`ADV-DEFINER-01`, `ADV-MASK-01`) under the same rule. Advancement used the pre-stated criterion: the three
attacks with the lowest Acc@1 over all attempts on the primary weaker model, ties broken by MRR.

- `ADV-DEFINER-01` and `ADV-MASK-01` gave Sonnet 0/3 each (every answered run wrong, or no answer) and Haiku 0/3 each.
- `ADV-LEX-01` gave Sonnet one wrong ranking (decoy first), one right, one timeout.
- `ADV-DEPTH-01` gave Sonnet one right and two timeouts: the only answered run found the gold, so its low all-attempts score
  is exhaustion, not misattribution; it was not advanced.
- `ADV-REGISTRY-01`, `ADV-OVERLOAD-01`, `ADV-OWNER-01`: every answered Sonnet run correct (3/3 each). Haiku's misses on them are
  budget exhaustion with an empty ranking, the same behaviour it shows on the plain control variant.

Advanced to confirmation: `ADV-DEFINER-01`, `ADV-MASK-01`, `ADV-LEX-01`. Haiku was used as the screening "much weaker" model
only; its exhaustion rate made it uninformative for confirmation, and the brief's confirmation sample (n=10 weaker, n=5 Opus)
was run on Sonnet and Opus. The plain control variant (`CONVERSION-LONG-TREATMENT-01`, attack id `BASE-LONG`) was run three
times on Haiku and ten times on Sonnet to measure baseline exhaustion under the same protocol.

**What confirmation later showed about the screening sample.** Three runs per attack was enough to separate the two attacks that
broke Sonnet completely (`ADV-DEFINER-01`, `ADV-MASK-01`: still 0 hits at n=10) from the ones that did not, but the `ADV-LEX-01`
signal (one wrong ranking in two answers) was a small-sample artefact: at n=10 Sonnet put the gold first in five of six answers. A
three-run screen can rank attacks; it cannot certify a moderate effect.
