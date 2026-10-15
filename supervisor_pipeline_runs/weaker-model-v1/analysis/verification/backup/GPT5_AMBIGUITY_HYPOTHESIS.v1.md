# Are the gpt-5 timeouts caused by the introduced ambiguity?

**Answer: NOT SUPPORTED.** The ten timeouts are explained by a malformed-command loop (five runs), slow provider serving (one), a
correct submission rejected by the validator (one) and long hidden deliberation after the evidence was already on screen (three).
None of them shows the behaviour the ambiguity hypothesis predicts: competing owners revisited, alternation between explanations, or
matched completed runs committing much earlier. The three deliberation cases fit a weak "found but not committed" reading, but they
cannot be tied to the ambiguity (section H and Limits).

Hypothesis tested (supervisor): the ambiguity built into these instances does not make gpt-5 rank the wrong method first; it
raises uncertainty, so the agent keeps verifying, cannot commit, and exhausts the 300 s budget.

Data: the 27 valid gpt-5 runs on the nine held-out instances (10 timeouts, 17 completed and all correct), reconstructed from their
recorded timestamps (`timeline_runs.json`, `timeline_steps.json`), matched by instance (`GPT5_TIMEOUT_MATCHED_COMPARISON.md`),
decomposed in time (`time_decomposition.json`), blind-coded by two independent coders per timeout with adjudication
(`GPT5_TIMEOUT_BLIND_LABELS.json`), plus three bounded next-action replays (`replays/`). Medians; effect size is Cliff's delta
(timeouts minus completed; +1 means every timeout is higher). n = 10 against 17, so nothing here is a significance claim.

## The operational measures (A to H)

**A. Search after the gold.** Timeouts searched and read *less* after the gold than completed runs did: calls after the gold 5
against 7 (delta -0.25), searches 0.5 against 1, reads 2.5 against 3. They had more time left after the gold (median 230 s to the
kill against 98 s from gold to the submission request in completed runs), but they used it on fewer, slower steps: 3.5 tool calls
per minute against 7.3 (delta -0.61).

**B. Suspect churn.** Methods newly inspected after the gold: 10.5 against 15 (delta -0.09). Declared alternatives (decoys,
entry points, evidence methods) newly inspected after the gold: median 0 in both groups. The coders found 0 to 6 alternative
suspects per timeout after the gold, and 12 in one run (CTV-E65CBB/run-002), which were all read along its own call chain.

**C. Revisits.** Revisit reads 3 against 5 (delta -0.33); repeated identical commands median 0 in both. Timeouts did not loop
over the same evidence more than completed runs did.

**D. Verification looping.** Tests after the decisive evidence: median 0 in both groups, with at most one test in any timeout.
Probes (javac/jshell): none in either group. There was no extra test-driven verification.

**E. Commitment delay.** In completed runs, the time from the faulty line first appearing to the submission request ranged from 16
to 220 s (median 98 s). For timeouts it is censored at the kill (median 230 s), so a late commit is consistent with the data. But
the timeouts did no more work in that window (A), and their extra time went into slow or malformed steps (H).

**F. Contradictory hypotheses.** Not observable from text: gpt-5's assistant messages carry no visible text in any of the 27 runs,
because its reasoning is hidden and was not inspected. From actions, the coders saw alternation between competing explanations in
1 of 20 coder labels (no 12, not observable 7).

**G. Evidence sufficiency.** Before the kill, the gold's faulty line was displayed and the gold read in full in 9 of 10 timeouts.
The declared external evidence was displayed in 9 of 10, and the coders judged the evidence sufficient in 9 of 10. The failure
message was seen in only 2 of 10 timeouts and 5 of 17 completed runs. This is because 15 of 34 gpt-5 test calls failed with
"Failed to parse Java version", every one of them run through a login shell (`bash -lc`); gpt-5.5 never used one.

**H. Searching or attributing at the end?** Coders' end states: found but not committed 5, plausibly writing the answer 3, still
searching 2. Replays from the exact pre-timeout state (one request each; selection fixed beforehand):

- CTV-E04F64/run-005: the model submitted a correct ranking (gold first) in 35 s. It had already made a correct submission at step
  17, which the validator rejected for a duplicate method name across two overloads, and it was writing the replacement when the
  timer expired.
- CTV-7CE456/run-002: the next action was another read, not a submission.
- CTV-E65CBB/run-002: the next action was another shell command; 31 of its 45 commands had been malformed.

What each timeout's 300 s went to (`time_decomposition.json`; the categories are exclusive and sum to the wall time within 6 s):

| Run | Instance | Dominant sink | Coders' primary | Reading |
|---|---|---|---|---|
| CTV-E65CBB/run-002 | HB-MATH | malformed commands 249 s (31 of 45 calls) | TOOL_LOOP | tool-call format loop |
| CTV-9EB2B7/run-003 | HA-MATH | malformed 227 s + slow serving 52 s; never reached the gold | OTHER | format loop and a slow provider |
| CTV-E04F64/run-004 | HA-JACKSONCORE | malformed 213 s (19 of 32 calls) | GOLD_FOUND_BUT_NOT_TRUSTED (adjudicated) | format loop |
| CTV-9CE7EA/run-003 | HA-COMPRESS | malformed 207 s; probe before launch 28.8 s | OTHER | format loop and a slow provider |
| CTV-7CE456/run-003 | HC-JACKSONCORE | malformed 117 s + deliberation 110 s; gold reached at 211 s; probe 50.1 s | OTHER | format loop and a slow provider |
| CTV-E65CBB/run-004 | HB-MATH | slow serving 211 s (7 calls, about 1 output token/s); probe 66.9 s | OTHER | slow provider |
| CTV-E04F64/run-005 | HA-JACKSONCORE | deliberation 213 s, including a correct submission that was rejected | OTHER | committed; lost to the rejection |
| CTV-21982A/run-002 | HC-MATH | deliberation 166 s (two 73 s and 93 s turns, each ending in a confirmation read) | GOLD_FOUND_BUT_NOT_TRUSTED | found, not committed |
| CTV-21982A/run-004 | HC-MATH | deliberation 186 s + tests 56 s | GOLD_FOUND_BUT_NOT_TRUSTED | found, not committed |
| CTV-7CE456/run-002 | HC-JACKSONCORE | deliberation 176 s + a 59 s request pending at the kill | OVER_VERIFICATION | found, not committed |

No coder used OWNERSHIP_AMBIGUITY, ENTRY_POINT_COMPETITION or CONVENTION_AMBIGUITY, as primary or secondary, in any of the 20 labels.

## Against the brief's criteria

| Criterion for SUPPORTED | Observed |
|---|---|
| gold already discovered and read | yes, 9 of 10 |
| decisive evidence already available | yes, 9 of 10 (the failure message was usually absent, because the test environment broke) |
| timeouts spend substantially more time exploring competing suspects | no: fewer calls, fewer methods and fewer revisits after the gold; declared alternatives 0 against 0 |
| rationales or tool behaviour repeatedly reflect ownership or convention uncertainty | no ambiguity-family label in 20 coder labels; alternation in 1 of 20; reasoning text not observable |
| matched completed runs commit much earlier | completed runs took 16 to 220 s from faulty line to commit; on the timeouts' own instances, 119 to 186 s |

| Criterion for NOT SUPPORTED | Observed |
|---|---|
| timeouts dominated by slow steps, commands or tool overhead | yes in 6 of 10 (malformed-command loop in 5, slow serving in 1), plus one validator rejection |
| no extra ambiguity-related behaviour | yes (A to D) |
| failure to locate sufficient evidence | 1 of 10 (CTV-9EB2B7/run-003) |

## Limits

- **No unambiguous control.** All 27 gpt-5 runs are on instances built around an ambiguity (HA entry point, HB sink, HC
  convention), so "caused by the introduced ambiguity" cannot be tested against a version without it. The test here is whether the
  timeouts *behave* the way the hypothesis predicts. They do not.
- **The weak positive.** The three deliberation-dominated timeouts are on HC-MATH and HC-JACKSONCORE, two convention-attribution
  instances where *every* gpt-5 run, completed or not, spent 110 to 186 s in heavy hidden reasoning turns. HC-LANG shows none. That
  fits "some instances demand much more reasoning per step". It does not show that the ambiguity, rather than the arithmetic the
  fault needs (signed pooled means; surrogate offsets), is what demands it. The reasoning content is hidden and was not read.
- **Timing.** 9 of the 10 timeouts fall in the last 14 slots of the block (2026-10-13 13:47 to 15:10Z), the same window as the two
  excluded provider stalls and the slow health probes. All 7 runs on the first day completed.
