# Stage B follow-up: gpt-5 timeouts and the GPT-5.6 replication

*Honours project · fault-localisation benchmark · experiment weaker-model-v1. Markdown copy of the report page sent on 16 October 2026.*

- **To** Hong Jin
- **From** Shawn
- **Date** 16 October 2026
- **Data** gpt-5 runs 12–13 Oct (re-analysed) · gpt-5.5 Stage B 14 Oct (reference) · GPT-5.6 Stage B 15 Oct (new)

After the Stage B result on gpt-5.5, I ran the two follow-up studies we agreed on. Study 1 asks why gpt-5 timed out on the held-out set, and whether your ambiguity hypothesis explains it. Study 2 re-runs the exact Stage B benchmark on GPT-5.6, changing only the model.

## Summary

1. **What caused the ten gpt-5 timeouts.** In 9 of the 10 the agent had already read the faulty method in full. Six ran during a period when the provider served gpt-5 slowly, one was a correct answer rejected by the submission validator, and three spent longer deliberating after finding the gold. This also qualifies our earlier verdict that gpt-5 is "too weak at the frozen budget": it is partly a statement about serving speed that afternoon and three harness interactions, not only about the model.
2. **Your ambiguity hypothesis is NOT SUPPORTED as the reason these ten runs timed out.** The coders saw no behaviour pointing to competing owners or an unclear convention. The three deliberation runs fit the "keeps verifying, does not commit" pattern, but every gpt-5 run is on an ambiguity instance, so for those three the cause is INCONCLUSIVE. This does not settle whether the ambiguity lengthens gpt-5's runs in general.
3. **GPT-5.6 on Stage B** (gpt-5.5 in brackets): C00 15/15 (15/15), C01 15/15 (14/15), C10 15/15 (3/15), C11 11/15 (4/15).
4. **Most of the Stage B drop did not transfer.** In the 5-hop + lie cells GPT-5.6 scored 26/30, against 7/30 for gpt-5.5 (p = 1.3e-6). Under the preregistered rule this is ATTENUATED, by a single run: 27/30 would have been ELIMINATED. All four GPT-5.6 misses are in C11.
5. **All four GPT-5.6 misses read the gold and still ranked the facade first.** In each, the agent read the gold in full, named it in its evidence chain and placed the first wrong value at it, then ranked first the method the test calls. Both blind labellers coded all four as ENTRY_POINT_BIAS, gpt-5.5's most common failure.
6. **Across the three models.** On the held-out set no model ranks a gold it has read below another method: gpt-5 loses answers to timeouts, gpt-5.5 and GPT-5.6 are at ceiling. On Stage B, gpt-5.5 often diagnoses correctly and then ranks the facade first; GPT-5.6 does this rarely. gpt-5 never ran Stage B, so I do not claim a capability ladder.
7. **Next step: the decomposition block is proposed, not launched.** The preregistered rule recommends it. Going beyond the rule, I suggest running it on gpt-5.5 (about $26), where there is a −0.73 drop to take apart. As designed it does not test hop distance. The decision is yours.

| Question | Verdict | Note |
|---|---|---|
| Are the gpt-5 timeouts caused by the ambiguity? | **NOT SUPPORTED** | For why these 10 runs timed out. 3 runs are compatible with non-commitment; for those, **INCONCLUSIVE** |
| Does the Stage B drop transfer to GPT-5.6? | **ATTENUATED** | Chain cells 26/30 against 1-hop 30/30 (p = 0.11); one run from ELIMINATED |
| Should the decomposition be next? | **YOUR DECISION** | Recommended by the rule; suggested on gpt-5.5; nothing launched |

## Terms used below

- **Gold**: The method that holds the injected fault. In Stage B an independent audit confirmed it as the fault's unique owner under the refined single-owner rule; each bug has a recorded bypass that this rule does not count as a second owner.
- **Facade**: The public method the failing test calls. In Stage B the gold is never the facade.
- **Acc@1**: The share of runs that rank the gold first in their submitted ranking of ten methods.
- **C00 · C01**: 1-hop cells: the fault sits in a helper the facade calls, next to a correct sibling helper. C01 writes that sibling in a valid but odd-looking form.
- **C10 · C11**: Chain cells: the fault moved five hops below the facade, one hop in each of five existing classes of 1,500+ lines (drawn with your recipe's functions, extended from its two hosts to five), with a misleading procedural sentence in the facade's javadoc (the "lie"). C11 also writes one correct hop in the odd-looking form.
- **Classification**: Preregistered on the pooled chain cells: REPLICATED at 12/30 or fewer with a significant drop of at least 0.40 from the 1-hop cells; ATTENUATED at 13–26/30, or a smaller significant drop; ELIMINATED at 27/30 or more with no significant drop.
- **Failure labels**: ENTRY_POINT_BIAS: a miss that ranks the method the test calls (the facade) first; in Stage B the agent had usually placed the first wrong value at the gold beforehand (15 of gpt-5.5's 17 such misses, all 4 of GPT-5.6's). CONVENTION_PRIOR: the agent blames the method that states or applies a convention rather than the one that violates it (in Stage B, the Math facade, whose javadoc is the convention's only statement). ATTRIBUTION_FAILURE: the gold was read but another method was ranked first and no more specific label fits.

*1 · Study 1 · retrospective, gpt-5 not re-run*

## What happened in the ten gpt-5 timeouts?

On the nine held-out instances gpt-5 had 27 valid runs: 17 completed, all with the gold ranked first, and 10 timed out at 300 s. I rebuilt each run's timeline from the recorded timestamps and compared every timeout with the completed runs on the same instance. Two blind coders labelled each timeout, with an adjudicator for disagreements. I also made three one-request replays from the exact pre-timeout state (about $0.13).

gpt-5 has very little slack at the frozen budget: its completed runs used a median of **238 of the 300 seconds**. In **9 of the 10 timeouts** the agent had already displayed and read the faulty method in full; CTV-9EB2B7/run-003 is the exception.

*Where the ten timeouts came from*

| Group | Runs | What the record shows |
|---|---|---|
| Slow serving<br>6 runs | CTV-9CE7EA/run-003<br>CTV-9EB2B7/run-003<br>CTV-7CE456/run-003<br>CTV-E65CBB/run-004<br>CTV-21982A/run-002<br>CTV-21982A/run-004 | All ran between 14:05 and 15:05Z on 13 Oct, when every measurable run was served below 50 output tokens per second (10.1–49.3), against 69.4 before. None had produced more output before the kill than its completed comparator on the same instance. Three also lost much of their time to malformed commands. Slower serving is a sufficient account, but it does not show these runs would have committed. CTV-21982A/run-004 is a boundary case: its output equalled its comparator's, and both coders labelled it "found but not committed". |
| Rejected submission<br>1 run | CTV-E04F64/run-005 | It submitted the correct ranking. The validator rejected it because two overloads gave the same method name twice, and the run timed out while rewriting it. |
| Extra deliberation after the gold<br>3 runs | CTV-7CE456/run-002<br>CTV-E04F64/run-004<br>CTV-E65CBB/run-002 | At normal speed, these spent 168–193 s in heavy reasoning calls (1,000+ reasoning tokens) after finding the gold, against 117–150 s for their completed comparators. Two of the three were also in a malformed-command loop, and every heavy call in those two also emitted a malformed command, so part of that reasoning may have gone to repairing commands (the reasoning is hidden). Compatible with non-commitment; whether the ambiguity caused it is inconclusive. |

Coders' primary labels: OTHER 5 (command format, slow responses, rejected submission), GOLD_FOUND_BUT_NOT_TRUSTED 3 (two of them in the slow period), OVER_VERIFICATION 1, TOOL_LOOP 1. End states: found but not committed 5, plausibly writing the answer 3, still searching 2. Replays, one request each: the rejected run resubmitted a gold-first ranking in 35 s (whether the validator would accept it was not checked); one deliberation run read another file; another issued one more shell command. Two of the three open runs were replayed, one sample each, which cannot settle them.

*Runs on the six instances that had a timeout*

| When the run happened | Timed out |
|---|---|
| Slow-serving period (run slots 15–25) | 6 of 6 |
| Rest of the block | 4 of 12 |

*After the gold, pooled medians: 9 timeouts that reached the gold vs 17 completed*

| Measure | Timeouts | Completed |
|---|---|---|
| Tool calls | 5 | 7 |
| Methods newly inspected | 13 | 15 |
| Reasoning tokens | 10,560 | 5,184 |
| Model time, as observed | 189 s | 98 s |
| Model time, re-timed at normal speed | 144 s | 96 s |

The slow period is defined by measured serving speed, not by where the timeouts fall. On the other three instances, 0 of 5 runs in it timed out, but those runs were lighter (median 7,089 output tokens). At the median the timeouts did not search or read more after the gold, but they did reason more; re-timing at normal speed removes about half of their extra model time. Within instances the picture is mixed: 6 of 9 inspected more methods than their comparator (several timeouts read whole files off the call chain, which the coders saw as confirmation or broad reading, not competing owners) and 5 of 9 reasoned more.

### Against the criteria in the brief

*Rows marked † would be expected for most runs that found the gold and then ran out of time, whatever the cause; the rows without † are the ones that separate ambiguity from other causes*

| Criterion | Observed |
|---|---|
| **For SUPPORTED** |  |
| Gold already discovered and read † | Yes, 9 of 10 |
| Decisive evidence already available † | Yes, 9 of 10, though the failure message was usually missing because tests broke |
| More time exploring competing suspects | No: fewer post-gold calls; declared alternatives newly inspected 0 against 0 |
| Behaviour reflects ownership or convention uncertainty | No ambiguity-type label in 20 coder labels; alternation between explanations in 1 of 20. The reasoning text is hidden. |
| Matched completed runs commit much earlier † | Yes in wall time, confounded by serving speed; holds at normal speed for the three deliberation runs |
| **For NOT SUPPORTED** |  |
| Timeouts dominated by slow serving, command problems or tool overhead | Yes for the 6 slow-period runs and the validator rejection; partly for 2 of the 3 deliberation runs (command loops) |
| No extra ambiguity-related behaviour | No competing-owner or convention behaviour seen; extra post-gold deliberation in 3 runs, which the hypothesis predicts but which is not specific to ambiguity |
| Failure to locate sufficient evidence | 1 of 10 |

> **Scope of the verdict.** NOT SUPPORTED answers why these ten runs timed out rather than completed. It does not say whether the ambiguity lengthens gpt-5's runs in general: every comparator is also an ambiguity run, and two of them needed 282 s and 291 s. Giving the three deliberation runs more weight would make the overall answer INCONCLUSIVE. A proper test would need same-bug controls without the ambiguity, a stable serving speed and a fixed shell environment, comparing post-gold reasoning rather than wall time. That is a new design, which I have not drawn up.

### Harness interactions found along the way

- gpt-5 often ends a shell command with a stray `}`: 16 of 27 runs (11 of them completed); 197 of 217 such commands failed.
- Tests launched through a login shell (`bash -lc`) failed on Java version detection in all 15 cases. gpt-5.5 used no login shell in its 27 held-out test commands.
- The submission validator rejects a ranking that names two overloads with one method name (3 gpt-5 runs, 2 recovered).

Stray braces were not counted for gpt-5.5 or GPT-5.6, nor login-shell tests for GPT-5.6, so neither is shown to be specific to gpt-5; the overload rule applies to any model. The frozen protocol and gpt-5's accuracy figures are unchanged.

*2 · Study 2 · preregistered replication*

## Does the Stage B drop transfer to GPT-5.6?

I re-ran the exact Stage B benchmark with only the model changed: the same 12 instances, gold methods, prompt, budgets (50 tool calls, 5 test runs, 300 s), run order and scoring. The classification and decision rules were preregistered before any GPT-5.6 call on a Stage B instance. The block produced 61 records: 60 valid runs, all answered, and one provider stall replaced under the frozen rule. Every record served gpt-5.6 at medium effort, with no contamination and all integrity checks passing.

*Chart (in the web version): Acc@1 out of 15 runs per cell (three bugs × five runs). C00: gpt-5.5 15, GPT-5.6 15. C01: gpt-5.5 14, GPT-5.6 15. C10: gpt-5.5 3, GPT-5.6 15. C11: gpt-5.5 4, GPT-5.6 11.*

*Acc@1 by cell with Wilson 95% intervals; p compares the two models (two-sided Fisher exact)*

| Cell | gpt-5.5 | GPT-5.6 | GPT-5.6 − gpt-5.5 | p (between models) |
|---|---|---|---|---|
| C00 · 1-hop, plain | 15/15 (0.80–1.00) | 15/15 (0.80–1.00) | 0.00 | 1.0 |
| C01 · 1-hop, odd sibling | 14/15 (0.70–0.99) | 15/15 (0.80–1.00) | +0.07 | 1.0 |
| C10 · 5-hop + lie | 3/15 (0.07–0.45) | 15/15 (0.80–1.00) | +0.80 | 1.1e-5 |
| C11 · 5-hop + lie + odd hop | 4/15 (0.11–0.52) | 11/15 (0.48–0.89) | +0.47 | 0.027 |
| 1-hop pooled (C00 + C01) | 29/30 (0.83–0.99) | 30/30 (0.89–1.00) | +0.03 | 1.0 |
| 5-hop + lie pooled (C10 + C11) | 7/30 (0.12–0.41) | 26/30 (0.70–0.95) | +0.63 | 1.3e-6 |

*Preregistered contrasts within each model (difference = second arm − first; two-sided Fisher exact)*

| Contrast | gpt-5.5 | p | GPT-5.6 | p |
|---|---|---|---|---|
| P1 · C00 vs C10 | −0.80 | 1.1e-5 | 0.00 | 1.0 |
| P2 · C01 vs C11 | −0.67 | 4.8e-4 | −0.27 | 0.10 |
| P3 · chain effect, 1-hop vs 5-hop + lie pooled | −0.73 | 3.4e-9 | −0.13 | 0.11 |
| Odd-hop effect, plain vs odd pooled | 0.00 | 1.0 | −0.13 | 0.11 |
| S2 · C10 vs C11 | +0.07 | 1.0 | −0.27 | 0.10 |
| Interaction (C11 − C01) − (C10 − C00) | +0.13 | not tested | −0.27 | not tested |

*By project (Wilson 95% intervals on the pooled chain cells; p compares the two models on the pooled chain cells, two-sided Fisher exact)*

| Bug | 1-hop, both cells | C10 | C11 | 5-hop + lie pooled | p |
|---|---|---|---|---|---|
| **Lang · StringUtils.indexOfAnyBut (gold isAnyOf)** |  |  |  |  |  |
| gpt-5.5 | 9/10 | 1/5 | 0/5 | 1/10 (0.02–0.40) | 0.0055 |
| GPT-5.6 | 10/10 | 5/5 | 3/5 | 8/10 (0.49–0.94) | 0.0055 |
| **Chart · DatasetUtilities.findStackedRangeBounds (gold signedSums)** |  |  |  |  |  |
| gpt-5.5 | 10/10 | 2/5 | 4/5 | 6/10 (0.31–0.83) | 0.63 |
| GPT-5.6 | 10/10 | 5/5 | 3/5 | 8/10 (0.49–0.94) | 0.63 |
| **Math · StatUtils.mode (gold tabulate)** |  |  |  |  |  |
| gpt-5.5 | 10/10 | 0/5 | 0/5 | 0/10 (0.00–0.28) | 1.1e-5 |
| GPT-5.6 | 10/10 | 5/5 | 5/5 | 10/10 (0.72–1.00) | 1.1e-5 |

GPT-5.6 is at or above gpt-5.5 in 11 of the 12 project-by-cell entries; the exception, Chart C11 (3/5 against 4/5), is within noise. The recovery is largest where gpt-5.5 had the most room to recover (Math and Lang).

> **Classification under the preregistered rule: ATTENUATED.** The chain cells pooled 26/30, at the top of the ATTENUATED band (13–26 of 30); ELIMINATED needed 27/30. The 95% interval for 26/30 (0.70–0.95) spans the ELIMINATED threshold (27/30 = 0.90), so in substance the result is hard to tell from ELIMINATED. Counting the excluded stall as a miss, instead of its valid replacement, gives 25/30, still ATTENUATED.
>
> **The shape differs from gpt-5.5.** On GPT-5.6 the plain chain (C10) is at ceiling and all four misses sit in C11, two in Lang and two in Chart. On gpt-5.5 the odd-looking hop made no difference. Every GPT-5.6 contrast rests on the same four misses, and four in fifteen is within sampling noise of zero (p = 0.10), so the C11 residual is not an established effect. No GPT-5.6 miss ranked the odd hop first, so if the odd hop matters, it does not do so by drawing the blame.
>
> **Against the expectation I preregistered.** Both parts were met: ATTENUATED or ELIMINATED, and misses of gpt-5.5's shape. I did not anticipate that every miss would fall in C11 while C10 stayed at ceiling.

### The misses: blind failure-mode labels

Each miss was labelled by two blind labellers (a process lens and an argument lens) using the unchanged Stage B brief, with an adjudicator for disagreements. The four GPT-5.6 misses are CTV-5818E6/run-001 and run-003 (Lang, gold ranked 2nd and 3rd) and CTV-E94DC6/run-002 and run-005 (Chart, gold ranked 2nd). The labellers agreed on all four primary labels.

| Label or check | gpt-5.5 (24 misses) | GPT-5.6 (4 misses) |
|---|---|---|
| Primary ENTRY_POINT_BIAS | 17 | 4 |
| Primary CONVENTION_PRIOR | 6 (all Math) | 0 |
| Primary ATTRIBUTION_FAILURE | 1 (odd hop ranked first) | 0 |
| Secondary EVIDENCE_INTEGRATION_FAILURE | 3 | 2 |
| Gold named in the final evidence chain | 24 of 24 | 4 of 4 |
| First wrong value placed at the gold | 22 of 24 | 4 of 4 |
| Facade ranked first | 23 of 24 | 4 of 4 |
| Facade lie quoted or paraphrased in the evidence chain | 0 | 0 |
| Rank-1 answer defensible | no 14 · partly 10 | no 4 |

"Defensible" asks whether a careful engineer would accept the rank-1 method as the fault location. Nine of gpt-5.5's ten "partly" answers are on Math, under the adjudicator's rule that a rank-1 method whose own documentation states the violated obligation is partly defensible (only the facade's javadoc states the NaN convention). The tenth is the Lang C01 miss, rated partly because the sibling implementations hold the surrogate logic inline. The stated reasons for ranking the facade first echo gpt-5.5's, for example "the direct production entry point".

*The brief's label-comparison questions*

| Question | Answer |
|---|---|
| Is ENTRY_POINT_BIAS eliminated? | No. It is GPT-5.6's only failure mode (4 of 4 misses), but it fell from 17 of 60 runs to 4 of 60. It is gone from C10 (gpt-5.5 had 8 such primaries there) and halved in C11 (8 to 4). |
| Is the gold articulated but the facade chosen? | Yes, in every GPT-5.6 miss. Among gpt-5.5's 24 misses the gold is named in all 24 and the facade ranked first in 23. |
| Is extra evidence retrieved? | No measurable difference. GPT-5.6 makes more search calls but reads fewer files; declared evidence was displayed in 30 of 30 chain runs for both models, independent probes 7/30 against 5/30, failure values 26/30 against 24/30. |
| Is the lie rejected? | Not measurable. A phrase scan of all 60 chain-cell evidence chains found no quotation or close paraphrase of the lie from either model, and the labels agree for the misses. The scan cannot show whether the lie was read, used or discounted. For gpt-5.5 the lie was on screen in 14 of 23 chain misses, and since it credits the facade with the computation, it could favour a facade-first ranking without being quoted. The decomposition's lie-on/lie-off arm would test this. |
| Is fault location kept apart from the entry point? | GPT-5.6 ranked the gold above the facade in 26 of 30 chain runs, gpt-5.5 in 8 of 30. In its 4 misses GPT-5.6 located the fault at the gold and still ranked the entry point first. The 26 correct runs were not labelled, so whether their reasoning differs from the misses' is not measured. |

### Process measures (5-hop + lie cells, medians per run)

| Measure | gpt-5.5 | GPT-5.6 |
|---|---|---|
| MRR | 0.578 | 0.928 |
| Gold displayed and read in full | 27 of 30 | 30 of 30 |
| Gold exposed but misranked | 20 | 4 |
| Tool calls | 19 | 29.5 |
| Searches | 15.5 | 25 |
| Files read | 19.5 | 15 |
| Step of the first gold display | 11 | 23 |
| Seconds to the first gold display | 30.5 | 40.5 |
| Tool calls after the first gold display | 7.5 | 6 |
| Reasoning tokens | 1,898 | 1,098 |
| Wall time | 82.0 s | 73.7 s |
| Cost per run | $0.43 | $0.28 |

GPT-5.6 makes more search calls before it reaches the gold, then commits with fewer calls after it; it does not read more. Its reasoning-token count is lower in every cell, including the 1-hop cells (916 against 1,432), which looks like a difference between the models rather than less deliberation. Token counts from two models are not a common scale, and within GPT-5.6 reasoning rises by about a fifth in the chain cells. The four wrong GPT-5.6 runs made slightly more tool calls than the six correct C11 runs on the same bugs (34.5 against 30.5, overlapping ranges, description only), so the extra search cannot be shown to cause the recovery.

### The brief's five questions

| Question | Answer |
|---|---|
| Do C10 and C11 still reduce accuracy? | C10 does not (15/15). C11 is lower, 11/15 against 15/15 in C01 (p = 0.10), but not established. |
| Replicated, attenuated or eliminated? | ATTENUATED under the preregistered rule, one run from ELIMINATED. Most of gpt-5.5's collapse did not transfer. |
| Do wrong runs find the gold, identify the faulty line and still rank the facade first? | Yes, all 4. |
| Does GPT-5.6 recover? | Largely: fully in C10 (3/15 → 15/15), partly in C11 (4/15 → 11/15). |
| Does it spend more effort but recover? | More search calls, not more reading, and fewer reasoning tokens than gpt-5.5. Whether the extra search causes the recovery cannot be shown with two models. |

*3 · Synthesis*

## gpt-5, gpt-5.5 and GPT-5.6 side by side

*The three models on the shared held-out set and on Stage B*

| Measure | gpt-5 | gpt-5.5 | GPT-5.6 |
|---|---|---|---|
| Held-out set (9 instances), Acc@1 | 17/27; all 10 failures are timeouts (7 with an operational account, 3 inconclusive) | 27/27 | 43/44 (reference from the previous experiment under the same protocol, not re-run; 1 no-answer) |
| Held-out: gold read but misranked | 0 | 0 | 0 |
| Stage B 1-hop cells | not run | 29/30 | 30/30 |
| Stage B 5-hop + lie cells | not run | 7/30 | 26/30 |
| Stage B: gold read but misranked | not run | 20 of 23 chain misses (the other 3 are a display-matcher gap) | 4 of 4 |
| Typical failure | Runs out of time, usually after reading the gold | Names the gold, ranks the facade first | The same, rarely, and only in C11 |

What the data do not support:

- A capability ladder across the three models: gpt-5 never ran Stage B, and its held-out losses are timeouts rather than misattributions.
- A capability explanation of the Stage B difference: two models also differ in serving speed, command habits, price and training data.
- Support from Stage A for the C11 residual. GPT-5.6 also failed CHART-PIE-TREATMENT-03 (0/5), a chain whose correct hop reads backwards, but gpt-5.5 also scored 0/5 there while showing no odd-hop effect in Stage B, the instance bundles an ownership split and was chosen because GPT-5.6 failed it, and that GPT-5.6 figure is a September run made before the frozen protocol.

*4 · Decision needed*

## Next step: the decomposition block

The preregistered rule recommends the decomposition after an ATTENUATED result, but it does not say on which model. Had the result been ELIMINATED (27/30), the rule would have allowed no decomposition without your approval.

The design I described after Stage B keeps every cell at 5 hops and crosses two factors: hops inside the facade's own class against hops dispersed across five host classes, and the facade lie on against off (three bugs, five runs per cell, 60 runs). It therefore does not test hop distance, although my earlier update and the preregistration's shorthand both mentioned it, and "dispersal" still bundles host size and anonymous placement.

| Option | What it would show | Estimated cost |
|---|---|---|
| Run it on gpt-5.5 (suggested) | Whether dispersal or the lie drives gpt-5.5's −0.73 drop. It bears on the gap with GPT-5.6 only if GPT-5.6 is at ceiling in every cell, which is expected but not measured. | about $26 |
| Run it on GPT-5.6 | Low expected yield, unmeasured: one of its four cells is C10, already 15/15. The other three are untested on GPT-5.6; I expect them near ceiling on the assumption that removing a component does not make the task harder, but the in-class arm also changes where the hops sit relative to the facade. GPT-5.6's one residual, the odd-hop chain cell, would need a different and smaller question that I have not designed. | about $16–17 |
| Stop here | Report Stage B as a gpt-5.5 effect that largely disappears on GPT-5.6. This departs from the preregistered recommendation. | $0 |

Choosing gpt-5.5 is my suggestion and goes beyond the rule. Nothing has been launched. The gpt-5.5 figure uses its chain-cell cost of $0.43 per run; the GPT-5.6 figure, computed for this report, uses its chain-cell cost of about $0.27–0.28 per run. Because the ATTENUATED class rests on a single run, I would rather you decide whether to run the decomposition and on which model.

*5 · Caveats*

## Limits

- Stage B has three bugs and 15 runs per cell. The GPT-5.6 residual depends on four misses.
- Two models on Stage B support a descriptive comparison only, not a causal claim about capability.
- Every gpt-5 held-out run is on an ambiguity instance, so Study 1 tests behaviour, not cause.
- The frozen provider-stall rule (the last event is a tool result that arrived more than 60 s before the kill, so a request had been pending for over 60 s) excluded five gpt-5 runs. All five had read the gold and had a request pending for 66–131 s, which is what either a long deliberation or a submission looks like. All Study 1 counts are conditional on this rule.
- The Study 1 coders were primed: the brief's examples for OTHER named slow responses and a submission in progress, and their timing tables gave no speed baseline, so some labels may partly reflect slowness.
- The Stage B labellers were not told the model or the cell, but the variant patch they read shows the cell's structure, and the name of the trajectory-view folder marks the GPT-5.6 runs as a second set.
- The lie was measured as cited or not (and, for gpt-5.5 only, displayed or not). Whether it was used or discounted is not measured for either model.
- The Study 1 speed threshold (50 tokens/s) was chosen after looking at the data. Every measurable slow-period run is at or below 49.3 and every other measurable run at or above 58.9, so any threshold in that gap gives the same period.

*6 · Accounting*

## Cost and records

*Spend (USD)*

| Item | USD |
|---|---|
| GPT-5.6 Stage B block (61 records) | 13.03 |
| Re-acceptance smoke run | 0.26 |
| gpt-5 replays (estimate) | 0.13 |
| Health probes (estimate) | 0.56 |
| This round, with estimates | about 14.0 |
| Experiment to date, recorded run cost | 64.10 |
| Experiment to date, with estimates | about 66.25 |

> **Where everything is.** All documents, run-level results, labels, sanitised derived data, the amendment log and the cost ledger are on GitHub: [Loongshow/d4j-variant, branch `claude/weaker-model-stageB-gpt56`](https://github.com/Loongshow/d4j-variant/tree/claude/weaker-model-stageB-gpt56/supervisor_pipeline_runs/weaker-model-v1) (commit `ab65f6f9`).
>
> Start with `supervisor_pipeline_runs/weaker-model-v1/gpt5-timeouts/GPT5_TIMEOUT_ANALYSIS.md` and `supervisor_pipeline_runs/weaker-model-v1/stageB-gpt56/GPT56_STAGE_B_RESULTS.md`.
>
> In this repository, relative to this file:
> - Study 1: [GPT5_TIMEOUT_ANALYSIS.md](../gpt5-timeouts/GPT5_TIMEOUT_ANALYSIS.md), [GPT5_AMBIGUITY_HYPOTHESIS.md](../gpt5-timeouts/GPT5_AMBIGUITY_HYPOTHESIS.md), [GPT5_TIMEOUT_MATCHED_COMPARISON.md](../gpt5-timeouts/GPT5_TIMEOUT_MATCHED_COMPARISON.md)
> - Study 2: [GPT56_STAGE_B_PREREGISTRATION.md](GPT56_STAGE_B_PREREGISTRATION.md), [GPT56_STAGE_B_RESULTS.md](GPT56_STAGE_B_RESULTS.md), [GPT55_VS_GPT56_ANALYSIS.md](GPT55_VS_GPT56_ANALYSIS.md), [CROSS_MODEL_FAILURE_MODES.md](CROSS_MODEL_FAILURE_MODES.md), [GPT55_VS_GPT56_STAGE_B.csv](GPT55_VS_GPT56_STAGE_B.csv)
> - Amendment log [AMENDMENTS.md](../AMENDMENTS.md) (W18 to W21) and [COST_LEDGER.csv](../COST_LEDGER.csv)
> - Open questions for you, in English and Chinese: [SUPERVISOR_QUESTIONS_2026-10-16.md](SUPERVISOR_QUESTIONS_2026-10-16.md)
>
> The gpt-5.5 Stage B records are unchanged, and their cell table regenerates byte for byte. Raw provider output, workspaces and credentials are not published.

---

Every run in both studies used the frozen protocol: the same base prompt, 50 tool calls, 5 test runs, 300 s and medium reasoning effort; only the model differs between blocks.

Statistics: Acc@1 = gold ranked first; Wilson 95% intervals; two-sided Fisher exact tests. Figures come from study documents that went through independent verification against the run records; the cost totals, the GPT-5.6 decomposition estimate and the per-project intervals were computed for this report.

Both studies went through independent verification rounds. The first Study 1 round led me to separate the model's own workload from the provider's serving speed; the second, to define the slow period by measured speed.
