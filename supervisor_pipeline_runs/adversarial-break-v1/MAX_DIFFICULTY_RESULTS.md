# Maximum-difficulty composite (Part 17): ADV-COMPOSITE-01

Protocol v2 (frozen prompt, 50 tool calls, 5 test runs, 300 s, structured submission) with one deviation from the GPT-5.6 runs: `defects4j test` could not execute for the Claude agents (`diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`). Provider errors and provider stalls are excluded from every denominator (`diagnostic/PROVIDER_STALL_RULE.md`).

Design and pre-registered gold: `TOP5_ATTACKS.md` (last section) and `construction/packages/ADV-COMPOSITE-01/attack.json`.
The composite is `ADV-DEFINER-01` plus gold witness removal, guard padding, a loud correct terminal and boolean-only trigger assertions.
Plan: claude-sonnet-4-6 x10, claude-opus-5-5 x5. Acc@1 is reported over answered runs and over all attempts the agent was allowed
to finish (timeouts and budget exhaustion count as misses; provider errors are excluded).

Protocol v2 (frozen prompt, 50 tool calls, 5 test runs, 300 s, structured submission) with one deviation from the GPT-5.6 runs: `defects4j test` could not execute for the Claude agents (`diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`). Provider errors and provider stalls are excluded from every denominator (`diagnostic/PROVIDER_STALL_RULE.md`).

| Attack | Model | answered / attempted | Acc@1 (answered) | Acc@1 (all attempts) | label (all) | no-answer (budget/time) | provider errors | MRR | gold ranks | gold discovered | gold in top-10 | tool calls | first gold | rank-1 roles | failure taxonomy | cost USD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `MAX-01` | claude-sonnet-4-6 | 5/10 | 0.0 | **0.0** | VERY STRONG | 5 | 0 | 0.2 | [5, 5, 5, 5, 5] | 5/5 | 5/5 | 45 | 14.8 | {"producer": 5} | {"OWNERSHIP_MISATTRIBUTION": 5} | 4.6071 |
| `MAX-01` | claude-opus-5-5 | 5/6 | 0.2 | **0.2** | VERY STRONG | 0 | 1 | 0.467 | [1, 3, 3, 3, 3] | 5/5 | 5/5 | 7.4 | 4.6 | {"gold": 1, "producer": 4} | {"OWNERSHIP_MISATTRIBUTION": 4} | 0.5748 |

## Composite (MAX-01 = ADV-COMPOSITE-01) versus its clean core (CMB-01 = ADV-DEFINER-01)

| Model | attack | answered/attempted | Acc@1 all | MRR | gold ranks | rank-1 roles | mean tool calls |
|---|---|---|---|---|---|---|---|
| claude-haiku-4-5 | `CMB-01` | 0/3 | 0.0 | - | [] | {} | - |
| claude-sonnet-4-6 | `CMB-01` | 7/11 | 0.0 | 0.2 | [5, 5, 5, 5, 5, 5, 5] | {"producer": 7} | 44 |
| claude-sonnet-4-6 | `MAX-01` | 5/10 | 0.0 | 0.2 | [5, 5, 5, 5, 5] | {"producer": 5} | 45 |
| claude-opus-5-5 | `CMB-01` | 5/5 | 0.0 | 0.433 | [2, 3, 2, 2, 3] | {"producer": 5} | 6.2 |
| claude-opus-5-5 | `MAX-01` | 5/6 | 0.2 | 0.467 | [1, 3, 3, 3, 3] | {"gold": 1, "producer": 4} | 7.4 |

## Per-run detail

| Model | Run | status | gold rank | rank-1 | rank-1 role | gold first exposed (step) | tool calls | cost USD | class |
|---|---|---|---|---|---|---|---|---|---|
| claude-opus-5-5 | run-001 | completed | 1 | `Plot::resolve` | gold | 5 | 10 | 0.1365614 | **CORRECT** |
| claude-opus-5-5 | run-002 | provider_stall | None | `None` | other | None | 1 | 0.015431 | **INFRASTRUCTURE** |
| claude-opus-5-5 | run-003 | completed | 3 | `PlotUtilities::drift` | producer | 4 | 6 | 0.1018606 | **OWNERSHIP_MISATTRIBUTION** |
| claude-opus-5-5 | run-004 | completed | 3 | `PlotUtilities::drift` | producer | 5 | 8 | 0.11750580000000001 | **OWNERSHIP_MISATTRIBUTION** |
| claude-opus-5-5 | run-005 | completed | 3 | `PlotUtilities::drift` | producer | 4 | 6 | 0.09747000000000001 | **OWNERSHIP_MISATTRIBUTION** |
| claude-opus-5-5 | run-006 | completed | 3 | `PlotUtilities::drift` | producer | 5 | 7 | 0.1059852 | **OWNERSHIP_MISATTRIBUTION** |
| claude-sonnet-4-6 | run-001 | invalid_ranking | None | `None` | other | 14 | 50 | 0.49388924999999995 | **NO_VALID_RANKING_BUDGET** |
| claude-sonnet-4-6 | run-002 | completed | 5 | `PlotUtilities::drift` | producer | 15 | 43 | 0.4450077000000002 | **OWNERSHIP_MISATTRIBUTION** |
| claude-sonnet-4-6 | run-003 | invalid_ranking | None | `None` | other | 14 | 52 | 0.5094104999999999 | **NO_VALID_RANKING_BUDGET** |
| claude-sonnet-4-6 | run-004 | invalid_ranking | None | `None` | other | 14 | 50 | 0.44368305000000013 | **NO_VALID_RANKING_BUDGET** |
| claude-sonnet-4-6 | run-005 | invalid_ranking | None | `None` | other | 14 | 51 | 0.49650735 | **NO_VALID_RANKING_BUDGET** |
| claude-sonnet-4-6 | run-006 | completed | 5 | `PlotUtilities::drift` | producer | 14 | 42 | 0.39104715 | **OWNERSHIP_MISATTRIBUTION** |
| claude-sonnet-4-6 | run-007 | completed | 5 | `PlotUtilities::drift` | producer | 15 | 41 | 0.38374905000000004 | **OWNERSHIP_MISATTRIBUTION** |
| claude-sonnet-4-6 | run-008 | completed | 5 | `PlotUtilities::drift` | producer | 13 | 50 | 0.4786848 | **OWNERSHIP_MISATTRIBUTION** |
| claude-sonnet-4-6 | run-009 | invalid_ranking | None | `None` | other | 13 | 50 | 0.47154720000000006 | **NO_VALID_RANKING_BUDGET** |
| claude-sonnet-4-6 | run-010 | completed | 5 | `PlotUtilities::drift` | producer | 17 | 49 | 0.49355234999999986 | **OWNERSHIP_MISATTRIBUTION** |

## Reading

**Opus, five valid attempts (one provider stall excluded, replacement run added): gold ranks 1, 3, 3, 3, 3; Acc@1 0.20 (VERY STRONG by the
brief's threshold); MRR 0.47.** The definer `PlotUtilities.drift` was ranked first in all four misses, exactly as in
`ADV-DEFINER-01` (five of five). The composite therefore did not add to the clean core's effect on Opus: `ADV-DEFINER-01`
already gave Acc@1 0.0 (ranks 2, 3, 2, 2, 3; MRR 0.43), and the composite gave 0.2 (MRR 0.47). What changed is the
position of the gold in the misses: the extra manipulations pushed it from rank 2 to rank 3 (the loud terminal `shift`
or the shallow adapter `rim` took second place), but they also produced the one hit.

**Why the one hit happened.** In run-001 Opus's caller search was `grep -rn "\.shift(\|\.drift(\|\.resolve(\|\.rim(" source tests`,
i.e. it searched the `tests` tree as well as `source`. That surfaced `PlotUtilitiesTests.testDrift`, Opus read it (step 10) and
concluded "drift is checked by PlotUtilitiesTests, so the bug is most likely the + in Plot.resolve". In runs 003 to 006 the caller
searches were confined to `source` (or omitted), the pin was never seen, and Opus repeated the `ADV-DEFINER-01` verdict word for
word: "drift has the sign reversed". The hit was not produced by any of the stacked manipulations; it was produced by one
broader search command that happened to include the tests directory, which Opus issues in roughly one run in five.

**Which stacked manipulations were inert on Opus, and why.**
- *Boolean-only failure signal.* Opus never needed the `expected:<87.5> but was:<112.5>` text: it hand-simulates the first
  assertion from the test source, which the task prompt includes, so the numbers 87.5 and 100 are always available. All five
  answered runs contain the hand-computed "112.5 vs 87.5" argument. Coarsening the assertion changed nothing.
- *Guard padding.* Opus followed `grep -n " resolve(" -A20` with `sed -n 1530,1590p`, i.e. it read the whole method the moment the
  window cut it off. The padding cost one tool call and hid nothing.
- *Witness removal at the gold.* Renaming `nudge` to `resolve` and stripping its javadoc did not change how Opus treated the
  method: in both attacks Opus reads the adapter as a faithful multiplier of whatever the definer supplies and looks for the sign
  error where the sign is defined.
- *Loud terminal.* `ShapeUtilities.shift` with the section-semantics javadoc was ranked second in one run (004) and fourth or
  lower otherwise; it never took first place.

**What actually carried the effect** is the single lever measured in the pilot and confirmed twice here: definer attribution.
Given an under-determined sign fault, Opus blames the method that defines the wrong-looking quantity rather than the
adapter that consumes it, and it does so with six to eleven tool calls, without running the failing test, and without
looking for a contract that pins the definer. The only thing that overturned it, in one run of eleven across the two attacks,
was reading the definer's unit test.

**Sonnet, ten attempts, none excluded: Acc@1 0.0 over all attempts and over answered runs (VERY STRONG).** Five runs answered, every one
with `PlotUtilities.drift` first and the gold `Plot.resolve` fifth behind `rim`, `ring` and `getArcBounds`, the identical ordering to all
seven Sonnet answers on `ADV-DEFINER-01`. The other five used the full 50-call budget without a valid submission (against three such runs
in ten valid attempts on `ADV-DEFINER-01`); four of them never submitted, one submitted a ranking with the gold fifth that the harness refused for a
non-existent filler method and then ran out of calls. Mean tool calls 47.8 against 43.3 on the core attack.

So for the weaker model the composite's extra manipulations did not move the gold in the answers it gave (rank 5 either way) but
turned answers into no-answers: the guard-padded, undocumented gold and the boolean-only assertions cost Sonnet enough calls that
half the runs ended in exhaustion. For Opus they were inert. Across both models the composite adds nothing to the attribution effect
of its clean core; what it adds is budget pressure on the model that already needed 40 to 50 calls.

**Composite versus core, both models.** Opus: core 0.0 (ranks 2, 3, 2, 2, 3), composite 0.2 (1, 3, 3, 3, 3). Sonnet: core 0.0 (ten
valid attempts, seven answers all rank 5), composite 0.0 (ten valid attempts, five answers all rank 5, five exhaustions). The
maximum-difficulty instance is therefore not harder than `ADV-DEFINER-01` in the sense that matters (where the gold lands when the
model answers); it is only more exhausting.
