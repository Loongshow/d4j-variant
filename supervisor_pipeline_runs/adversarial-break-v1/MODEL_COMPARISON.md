# Model comparison

Protocol v2 (frozen prompt, 50 tool calls, 5 test runs, 300 s, structured submission) with one deviation from the GPT-5.6 runs: `defects4j test` could not execute for the Claude agents (`diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`). Provider errors and provider stalls are excluded from every denominator (`diagnostic/PROVIDER_STALL_RULE.md`).

| Attack | claude-haiku-4-5 Acc@1 all (answered/attempted) | claude-sonnet-4-6 Acc@1 all (answered/attempted) | claude-opus-5-5 Acc@1 all (answered/attempted) | claude-haiku-4-5 MRR | claude-sonnet-4-6 MRR | claude-opus-5-5 MRR | transfers to Opus? |
|---|---|---|---|---|---|---|---|
| `BASE-LONG` | 0.333 (1/3) | 0.875 (7/13) | - | 1.0 | 1.0 | - | - |
| `CMB-01` | 0.0 (0/3) | 0.0 (7/11) | 0.0 (5/5) | - | 0.2 | 0.433 | yes |
| `CTX-01` | 0.0 (1/3) | 0.0 (8/16) | 0.4 (5/5) | 0.25 | 0.25 | 0.567 | yes |
| `DEP-01` | 0.333 (1/3) | 1.0 (1/3) | - | 1.0 | 1.0 | - | - |
| `LEX-01` | 0.333 (1/3) | 0.889 (9/14) | 1.0 (5/5) | 1.0 | 0.944 | 1.0 | no (both robust) |
| `MAX-01` | - | 0.0 (5/10) | 0.2 (5/6) | - | 0.2 | 0.467 | yes |
| `NAV-01` | 0.667 (2/3) | 1.0 (3/3) | - | 1.0 | 1.0 | - | - |
| `OVL-01` | 0.667 (2/3) | 1.0 (3/3) | - | 1.0 | 1.0 | - | - |
| `OWN-01` | 0.667 (2/3) | 1.0 (3/3) | - | 1.0 | 1.0 | - | - |

## Reading

**What transfers to Opus.** Definer attribution transfers completely: `ADV-DEFINER-01` gave Opus Acc@1 0.0 over five runs
(gold ranks 2, 3, 2, 2, 3) and `ADV-COMPOSITE-01` gave 0.2 over five valid runs (1, 3, 3, 3, 3). The depth prior transfers
partially: `ADV-MASK-01` gave Opus 0.4 (ranks 1, 4, 1, 3, 4), with the outcome decided by whether Opus read the second
consumer of the deepest hop. Witness inversion does not transfer: `ADV-LEX-01` gave Opus 1.0 over five runs, every run with
six to eight tool calls and the gold first.

**What separates the models.** Opus answers in six to eleven tool calls, never runs the failing test in these attacks, and
hand-simulates the assertion from the test source; when it is wrong it is wrong quickly and confidently, and the gold sits
at rank 2 or 3. Sonnet uses 40 to 51 tool calls, runs the failing test once, and either submits with the gold at rank 5 or
exhausts the budget or the 300 s deadline. Haiku exhausts the budget on every Chart attack and on two of three plain
control runs, so its Acc@1 over all attempts is dominated by baseline exhaustion rather than by any attack.

**Reading the "transfers to Opus?" column.** "yes" means both the primary weaker model and Opus are at or below 0.7 over all
attempts; "weaker-only" means only Sonnet is. The attacks whose effect rests on planted lexical material (`ADV-LEX-01`) or
on search cost (`ADV-REGISTRY-01`, `ADV-OVERLOAD-01`) are at best weaker-only; the attacks whose effect rests on an
attribution judgement the model makes after it has read everything (`ADV-DEFINER-01`, `ADV-MASK-01`, `ADV-COMPOSITE-01`)
transfer.

**Sonnet at ten valid attempts per attack (hung requests excluded, stalled attempts topped up).** `ADV-DEFINER-01` 0 hits in ten valid
attempts (seven answers, all gold rank 5). `ADV-MASK-01` 0 hits in ten valid attempts (eight answers, all gold rank 4). `ADV-LEX-01`
eight hits in nine answers. So the
weaker model agrees with Opus on what breaks (definer attribution, the depth prior) and on what does not (witness inversion); the
difference between the models is how far down the gold falls (rank 5 vs 2 to 3) and how often Sonnet fails to answer at all.
Composite: Opus 0.2 (1, 3, 3, 3, 3), Sonnet 0.0 (five answers all rank 5, five budget exhaustions). Control (plain
`CONVERSION-LONG-TREATMENT-01`): Sonnet answered seven of eight valid attempts with the gold first and exhausted once; Haiku answered
one of three (gold first) and exhausted twice. The control fixes the no-answer baseline that the all-attempts Acc@1 of the weaker
models must be read against: about one in eight for Sonnet, two in three for Haiku.
