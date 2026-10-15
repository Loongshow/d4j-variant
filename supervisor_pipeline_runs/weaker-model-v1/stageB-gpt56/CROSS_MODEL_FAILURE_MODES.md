# How gpt-5, gpt-5.5 and GPT-5.6 fail on the same instances

All three models ran under the frozen protocol: base prompt sha `845e21e7…`, 50 tool calls, 5 tests, 300 s, effort medium, and the
same harness. Only two instance sets were run on more than one model:

- **The held-out set:** nine instances whose gold is pinned by documentation. All three models ran it.
- **Stage B:** three fresh bugs in a 2×2 design. gpt-5.5 and GPT-5.6 ran it; gpt-5 did not.

Any statement about all three models is therefore limited to the held-out set. Stage A, the frozen breakers, was run on gpt-5.5
only and compared against GPT-5.6 references taken from other roots. It appears below as context.

## What each model loses, and how

| | gpt-5 | gpt-5.5 | GPT-5.6 |
|---|---|---|---|
| Held-out (9 instances), Acc@1 | 17/27; all 17 answered runs correct; 10 timeouts | 27/27 | 43/44; 1 no-answer (reference, mechanism-search-v1) |
| Held-out: gold read but misranked | 0 | 0 | 0 |
| Stage B 1-hop cells | not run | 29/30 | 30/30 |
| Stage B 5-hop + lie cells | not run | 7/30 | 26/30 |
| Stage B: gold read but misranked | not run | 20 of 23 chain misses (the other 3 are a display-matcher gap, W16) | 4 of 4 |
| Typical failure | runs out of time, usually after reading the gold | answers, names the gold, ranks the facade first | answers, names the gold, ranks the facade first, in the odd-hop chain cell only |

### gpt-5 (held-out only): timeouts, never misrankings

All ten failures are timeouts. In 9 of the 10, the gold had already been displayed and read in full (`../gpt5-timeouts/`).

- **Six** fell in a provider slow-serving period on 2026-10-13, in which every measurable run ran below 50 tok/s, against 69 before
  it.
- **One** had committed: the validator rejected its ranking because one method name appeared twice, from two overloads.
- **Three** ran 168 to 193 s of heavy reasoning after the gold, against 117 to 150 s in their comparators. Two of them were also in
  malformed-command loops. Their behaviour fits non-commitment, but whether the ambiguity caused it is INCONCLUSIVE.

gpt-5 never misranked a gold it had read. The first two groups (7 of 10) have a sufficient operational account; the third does
not.

Two harness interactions were recorded for gpt-5:
- a stray `}` in command strings, in 16 of 27 runs;
- login-shell test calls, which fail on Java version detection.

How far these interactions reach the other models:
- gpt-5.5 issued none of its 27 held-out test commands through a login shell.
- Stray braces, and login-shell tests by GPT-5.6, were not counted for the other models.
- The validator's duplicate-overload rule applies to any model.

### gpt-5.5 (held-out and Stage B): attribution after discovery

At ceiling on the held-out set. In Stage B, 24 misses: 23 in the chain cells and 1 in C01. Blind labels, two lenses per miss, with
adjudication:

| Label | gpt-5.5 (24 misses) | GPT-5.6 (4 misses) |
|---|---|---|
| primary ENTRY_POINT_BIAS | 17 | 4 |
| primary CONVENTION_PRIOR | 6 (all Math: the NaN convention is stated only in the facade's javadoc) | 0 (no Math miss) |
| primary ATTRIBUTION_FAILURE | 1 (the odd hop ranked first "as the method that forms the returned array") | 0 |
| secondary EVIDENCE_INTEGRATION_FAILURE | 3 | 2 |
| secondary LOCAL_ODDNESS_BIAS | 2 | 0 |
| secondary ENTRY_POINT_BIAS | 6 | 0 |
| secondary CONVENTION_PRIOR | 2 | 0 |
| facade ranked first | 23 of 24 | 4 of 4 |
| gold named in the final evidence chain | 24 of 24 | 4 of 4 |
| divergence located at the gold | 22 of 24 | 4 of 4 |
| facade lie cited | none (from the rationales; phrase scan 0 of 23 chain misses) | 0 of 4 (labels and phrase scan) |
| defensible | no 14, partly 10 (9 Math, under the facade-javadoc rule; 1 Lang C01) | no 4 |
| cells | C10 12, C11 11, C01 1 | C11 4 |
| lenses agreed on all three fields | 12 of 24 | 3 of 4 |

### GPT-5.6 (held-out and Stage B): the same failure, much rarer

All four misses are ENTRY_POINT_BIAS. In each, the agent:

1. displays and reads the gold in full;
2. names it in its evidence chain;
3. places the first wrong value at the gold's fault line;
4. ranks first the facade that the test calls, on stated grounds such as "the direct production entry point" or "the directly
   tested method and its immediate delegate are the highest-probability modification sites".

That is the gpt-5.5 failure, unchanged in form.

## Answers to the brief's comparison questions

**Is ENTRY_POINT_BIAS eliminated?** No. It is the only GPT-5.6 failure mode here, in 4 of 4 misses. But its frequency fell from 17 of
60 runs to 4 of 60.

It has gone from C10 entirely:
- gpt-5.5 missed 12 of 15 C10 runs, 8 of them with ENTRY_POINT_BIAS and 4 with CONVENTION_PRIOR as the primary label;
- GPT-5.6 missed none.

In C11 it fell from 8 primaries to 4.

**Is the gold articulated but the facade chosen?**
- In every GPT-5.6 miss (4 of 4). Among gpt-5.5's 24 misses, the gold is named in all 24 and the divergence is placed at it in 22.
  The facade is ranked first in 23; the remaining miss (CTV-7C06F2/run-003) ranked the odd hop `mostFrequent` first and the gold
  second.
- In the 26 correct GPT-5.6 chain runs the gold was ranked above the facade. Those runs were not labelled, because they are not
  misses, so whether their reasoning differs from the misses' is not measured.

**Is extra evidence retrieved?**
- **Search effort.** GPT-5.6 searches more in the chain cells: 29.5 tool calls and 25 searches against gpt-5.5's 19 and 15.5. It
  reaches the gold later, at step 23 against 11.
- **Evidence actually displayed.** No measure separates the models: declared evidence displayed in 30 of 30 runs for both;
  independent probes 7 of 30 against 5 of 30; failure values displayed 26 of 30 against 24 of 30.
- **Within GPT-5.6.** Against the six correct C11 runs on the same two bugs (Lang and Chart), the four misses made 34.5 tool calls
  against 30.5. Their first gold display came at step 29 against 26, and they made 5 post-gold calls against 2.5 (medians). The
  ranges overlap: two correct runs made 37 calls. With 4 runs against 6, this is description only.
- **More search is not more reading.** GPT-5.6's chain runs made more search calls but read fewer files than gpt-5.5's (15
  against 19.5) and about the same number of lines (1,381 against 1,332).

**Is the lie rejected?** It is not cited, and that is all the data show.
- No chain-cell evidence chain from either model contains a phrase from the lie: 0 of 60 in a keyword scan
  (`../scripts/stageB_lie_scan.py`, which detects quotation or close paraphrase, not use). The labels agree for the misses.
- Whether the lie was read, used, ignored or rejected is not measured.
  - For gpt-5.5, the safe views show the lie displayed in 14 of 23 chain misses (`../STAGE_B_RESULTS.md`).
  - For GPT-5.6, display was not measured.
- The lie describes the facade as doing the computation, so it could favour a facade-first ranking without being quoted.
- The lie-on/lie-off arm of the proposed decomposition would test its effect.

**Does it distinguish fault location from entry point?**
- **Correct runs.** GPT-5.6 ranked the gold first in 26 of 30 chain runs, against 7 of 30 for gpt-5.5. gpt-5.5 ranked the gold
  above the facade in 8 of 30: its 7 correct runs, plus the miss that put the odd hop first.
- **Misses.** In its 4 misses it located the fault at the gold and still ranked the entry point first, so in those runs it did not
  keep the two apart in the ranking.

## What the three models do not show

- **No ladder claim.** The shared data do not support a capability-ladder claim.
  - gpt-5 never ran Stage B.
  - On the held-out set, held-out Acc@1 is 0.63, 1.00 and 0.98, non-decreasing within noise. But gpt-5's losses there are
    timeouts, not misattributions: 7 of 10 have an operational account, and the other 3 are inconclusive.
  - gpt-5.5 and GPT-5.6 do not differ on the held-out set: 27/27 against 43/44.
- **No cause.** No claim that a capability causes the Stage B difference. With two models, differences in serving speed (GPT-5.6
  was faster), command habits, price and training data are not separated from capability.
- **No established interaction.** The GPT-5.6 residual sits where the chain and the odd-looking hop meet.
  - **Statistically:** it is 4 runs in 15 (p = 0.10 against C10). The interaction, P2, P3 and S2 all rest on the same four misses.
  - **The odd hop was not blamed:** no GPT-5.6 miss ranked it first or was labelled LOCAL_ODDNESS_BIAS. If the odd hop matters for
    GPT-5.6, it is not by drawing the blame.
  - **Stage A does not help.** GPT-5.6 scored 0/5 on the Stage A instance CHART-PIE-TREATMENT-03, a chain with a hop that reads
    backwards. But:
    - gpt-5.5 also scored 0/5 there, and shows no odd-hop effect in Stage B;
    - the instance bundles an ownership split and was chosen because GPT-5.6 failed it;
    - the GPT-5.6 reference is a September run made before the frozen protocol.

    So it does not bear on the difference between the models.
