# Validity block: `ADV-DEFINER-01` with an executable `defects4j test` (protocol v2+runner)

Why this exists: every Claude run in the main tables (and in the pilot) could not execute `defects4j test` because the servers lacked
`PERL5LIB`; the frozen GPT-5.6 runs could. See `diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`. This block re-runs only the headline
attack with the runner fixed (servers `opus55t`, `sonnet46t`), Opus x5 and Sonnet x5, and is never mixed into the main tables.

| Attack | Model | protocol | answered / attempted | Acc@1 (answered) | Acc@1 (all attempts) | MRR | gold ranks | rank-1 roles | test runs executed (mean) | tool calls | provider stalls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `CMB-01` | claude-sonnet-4-6 | v2 | 7/11 | 0.0 | **0.0** | 0.2 | [5, 5, 5, 5, 5, 5, 5] | {"producer": 7} | 1 | 44 | 1 |
| `CMB-01` | claude-opus-5-5 | v2 | 5/5 | 0.0 | **0.0** | 0.433 | [2, 3, 2, 2, 3] | {"producer": 5} | 0 | 6.2 | 0 |
| `CMB-01` | claude-sonnet-4-6 (v2+runner) | v2+runner | 4/5 | 0.0 | **0.0** | 0.2 | [5, 5, 5, 5] | {"producer": 4} | 1 | 42.8 | 0 |
| `CMB-01` | claude-opus-5-5 (v2+runner) | v2+runner | 5/5 | 0.2 | **0.2** | 0.6 | [2, 2, 2, 2, 1] | {"producer": 4, "gold": 1} | 0.2 | 6.6 | 0 |

## Per-run detail (v2+runner)

| Model | Run | status | gold rank | rank-1 | test runs | gold first exposed (step) | tool calls | cost USD | class |
|---|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 (v2+runner) | run-001 | completed | 2 | `PlotUtilities::drift` | 1 | 6 | 8 | 0.1176392 | **OWNERSHIP_MISATTRIBUTION** |
| claude-opus-5-5 (v2+runner) | run-002 | completed | 2 | `PlotUtilities::drift` | 0 | 4 | 6 | 0.08987620000000002 | **OWNERSHIP_MISATTRIBUTION** |
| claude-opus-5-5 (v2+runner) | run-003 | completed | 2 | `PlotUtilities::drift` | 0 | 5 | 6 | 0.087029 | **OWNERSHIP_MISATTRIBUTION** |
| claude-opus-5-5 (v2+runner) | run-004 | completed | 2 | `PlotUtilities::drift` | 0 | 4 | 6 | 0.0928384 | **OWNERSHIP_MISATTRIBUTION** |
| claude-opus-5-5 (v2+runner) | run-005 | completed | 1 | `Plot::nudge` | 0 | 4 | 7 | 0.11330180000000001 | **CORRECT** |
| claude-sonnet-4-6 (v2+runner) | run-001 | completed | 5 | `PlotUtilities::drift` | 1 | 14 | 43 | 0.3950530500000001 | **OWNERSHIP_MISATTRIBUTION** |
| claude-sonnet-4-6 (v2+runner) | run-002 | invalid_ranking | None | `None` | 2 | 15 | 54 | 0.51784785 | **NO_VALID_RANKING_BUDGET** |
| claude-sonnet-4-6 (v2+runner) | run-003 | completed | 5 | `PlotUtilities::drift` | 1 | 14 | 45 | 0.42781365 | **OWNERSHIP_MISATTRIBUTION** |
| claude-sonnet-4-6 (v2+runner) | run-004 | completed | 5 | `PlotUtilities::drift` | 1 | 13 | 47 | 0.42066195 | **OWNERSHIP_MISATTRIBUTION** |
| claude-sonnet-4-6 (v2+runner) | run-005 | completed | 5 | `PlotUtilities::drift` | 1 | 15 | 36 | 0.30742605 | **OWNERSHIP_MISATTRIBUTION** |

## Reading

**Opus (v2+runner, n=5).** Gold ranks 2, 2, 2, 2, 1; Acc@1 0.2; MRR 0.60, against 2, 3, 2, 2, 3 (Acc@1 0.0, MRR 0.43) under v2. One run
(run-001) executed `defects4j test` and received the real ant output (`Failing tests: 1 ... expected:<87.5> but was:<112.5>`); it still
ranked `drift` first with the same argument as every v2 miss. The other four runs issued no test command at all, exactly as under v2.
The single hit (run-005) came, as in the composite's single hit, from a caller grep over `source/ tests/` that surfaced
`PlotUtilitiesTests`, which Opus then read: "drift = p1-p2 is fixed by PlotUtilitiesTests.testDrift ... the sign error is in nudge".
Under either protocol the deciding event is reading the pinning test, not running the failing test. The headline result
therefore survives the test-runner fix on both models: definer attribution with a non-terminal gold gives Acc@1 0.0 to 0.2 across fifteen Opus runs
(five v2, five composite, five v2+runner), with both hits produced by one broader search command.

**Sonnet (v2+runner, n=5).** Gold ranks 5, 5, 5, 5 in the four answered runs and one budget exhaustion: Acc@1 0.0 over five valid attempts, the same as under v2 (ten valid attempts, seven answers all at rank 5). The failing test executed through ant in 5 of 5 runs and returned the real `expected:<87.5> but was:<112.5>` output; 1 of 5 runs opened the pinning unit test. Every answer ranked `drift` first with the same reasoning as under v2. For Sonnet the working test runner changed neither the verdict nor the ordering; the deviation is not what made Sonnet wrong on this attack.

**What the block does not claim.** It is five runs per model on one attack; it shows whether the strongest finding depends on the
missing runner, not what the whole root would look like under the fixed environment. The main tables stay under protocol v2.
