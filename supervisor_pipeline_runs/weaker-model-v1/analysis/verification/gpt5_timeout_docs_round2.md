# Round-2 verification of the gpt-5 timeout documents (2026-10-15)

This round used two independent verifier agents, a numbers lens and an inference lens. Neither could write to the root, and both
were barred from `.env`, `raw_agent_output.txt`, `_smoke` directories, probe files and hidden-reasoning fields. They checked the
revised `gpt5-timeouts/GPT5_TIMEOUT_ANALYSIS.md`, `GPT5_AMBIGUITY_HYPOTHESIS.md` and `GPT5_TIMEOUT_MATCHED_COMPARISON.md`, and
the W19 section of `AMENDMENTS.md`. The numbers lens re-ran the four `scripts/gpt5_*.py` scripts in a scratch mirror, and every
derived JSON and CSV came out byte-identical. Round 1 is recorded in `gpt5_timeout_docs_round1.json`.

## Numbers lens: 0 must-fix, 6 should-fix, 5 notes; every round-1 item fixed or partly fixed

| Item | Finding | Resolution |
|---|---|---|
| S1 | "15 of the 32 test steps" is wrong. It is 15 of the 34 commands; 13 of the 15 are frozen test steps | fixed in HYP G |
| S2 | "In-window submissions took 95 to 120 s" is wrong. They took 46.2 to 120.4 s (median 94.8) | fixed (HYP Limits and slow-period table) |
| S3 | The long waits are not two kinds. They are deliberation 38, slow serving 7 and neither 7 | fixed in MATCH; `facts.json` `long_waits_ge30s` |
| S4 | The verdict counts disagree (6+2+1 against 8 of 10) | fixed: verdict rewritten (see inference MF1, MF2) |
| S5 | CTV-E04F64/run-004 is counted both as a command loop and as unexplained by commands | fixed: it is read the same way as CTV-E65CBB/run-002 |
| S6 | The counterfactual is overstated: 3 of the 4 extra-work runs fall under 300 s | fixed: calibration added and the 266 to 298 s ends marked as within error |
| N1 | 69 against 70 against 70.4, and the 3-of-5 basis is not disclosed in ANA | fixed |
| N2 | 36.8 against 36.7 s (timeline against ledger) | disclosed in ANA |
| N3 | The probes ran 14:03 to 14:43Z, not 14:48 | fixed |
| N4 | "No visible text" was not written out. The duplicate-overload reason was not confirmed for 2 of 3. Some figures were missing from `facts.json` | added to `facts.json`: `assistant_messages_with_visible_text` (0 of 27), `validator_rejections` (all 3 `duplicate_method`), long-wait tallies |
| N5 | "+0%" is really -0.1% | fixed |

## Inference lens: 6 must-fix, 8 should-fix, 6 notes

The verifier's own verdict: NOT SUPPORTED is defensible as an explanation of why these 10 runs timed out, if the scope is stated.
With corrected counts, 2 to 3 runs are compatible with non-commitment, plus one boundary run and two censored unknowns. The call
therefore sits closer to INCONCLUSIVE than the documents had said.

| Item | Finding | Resolution |
|---|---|---|
| MF1 | CTV-E04F64/run-004 is counted both ways. CTV-E65CBB/run-002 has the same shape (cheap failed calls 72 s and 45 s; post-gold heavy calls 177 s and 168 s, all also malformed), yet is treated differently | both are now counted as compatible with non-commitment, with the command-loop entanglement stated (3 of 10). The overlapping "249 s" figure is removed |
| MF2 | "Explained without non-commitment" claims more than the output rule shows | reworded to "a sufficient account; non-commitment not ruled out". CTV-21982A/run-004 is named as the boundary case |
| MF3 | The replay inference "final call served slowly" does not follow: at least 59.4 s is about 4,100 tokens or more, which could be a submission or a deliberation | fixed in HYP H and in ANA |
| MF4 | The window was drawn around the timeouts (13:47Z, 51 s before slot 13) | the slow period is now defined by measured speed: slots 15 to 25. Timeout instances: 6 of 6 timed out inside it, 4 of 12 outside. `facts.json` `slow_period_by_speed` |
| MF5 | The agreement between speed and the output rule is largely by construction, since every timeout ran 300 s | the output comparison is now called a consistency check; its pooled-baseline sensitivity (7 of 10) is disclosed |
| MF6 | "All along the run's own call chain" is contradicted by the coders (off-path whole-file reads) | fixed: off-path reads listed; the coders read them as confirmation or broad reading |
| should | Stall censoring could hide mid-deliberation runs as well as mid-submission runs | fixed in HYP Limits; counts stated as conditional on the rule |
| should | The counterfactual needs calibration, and the 82 and 111 s ends are not completion estimates | calibration added (median +0.2 s, range -28.9 to +18.7 s on 12 runs); the two ends marked |
| should | The model-side signal is understated | re-timed post-gold model time added (144 against 96 s, delta 0.28); reasoning "roughly doubles" |
| should | The SERVING headline leaves out the command loops in three runs | fixed |
| should | Returns to the entry point or a decoy are not measured | disclosed. CTV-7CE456/run-002's re-reads at steps 14 and 15 are noted, and both coders read them as citation-gathering |
| should | "Repeatedly" was read as a count of runs | the verdict now rests on the content of the discriminating criteria |
| should | INCONCLUSIVE was not addressed and the scope was not stated | both are now addressed in the headline |
| should | "So search had finished" | changed to "gold displayed and read in full"; the coders' still-searching judgement for CTV-E65CBB/run-004 is noted |
| notes | pooled-baseline sensitivity; 0.6 s stall margin; E04F64/run-005's 153 s to first submission; slow-serving column; pace claim; HC deliberation | each added or corrected (the pace claim was removed) |
