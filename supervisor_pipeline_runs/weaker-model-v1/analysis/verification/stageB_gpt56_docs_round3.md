# Round-3 verification: Stage B GPT-5.6 documents (2026-10-15)

Two independent verifier agents reviewed the documents, one through a numbers lens and one through an inference lens. Neither was
allowed to write to the root. Both were barred from `.env` files, `raw_agent_output.txt`, `_smoke` directories, probe files,
`mini-swe-agent.traj.json` files and hidden-reasoning fields.

The documents covered were:
- `stageB-gpt56/GPT56_STAGE_B_RESULTS.md`
- `stageB-gpt56/GPT55_VS_GPT56_ANALYSIS.md`
- `stageB-gpt56/CROSS_MODEL_FAILURE_MODES.md`
- `stageB-gpt56/SUPERVISOR_UPDATE_STAGE_B_GPT56.md`
- the W20 section of `AMENDMENTS.md`
- `COST_LEDGER.csv`

Both verifiers independently recomputed every count, Wilson interval, Fisher p, MRR, process median and label tally. All of them
matched.

- The numbers verifier also reproduced `stageB_cells.json` and `stageB_cells_w56.json` byte for byte from a scratch copy of the
  report script.
- The inference verifier confirmed that the lie scan loaded all 60 submissions and that the quoted reasons appear verbatim in the
  rationales.

## Numbers lens: 2 must-fix, 4 should-fix, 7 notes

| Item | Finding | Resolution |
|---|---|---|
| must | `COST_LEDGER.csv` labels the wmDiag smokes as GPT-5.6; they ran gpt-5.5 | fixed; erratum in W20 |
| must | "gold above the facade … 7 of 30 for gpt-5.5" should be 8: CTV-7C06F2/run-003 ranked the odd hop first and the gold second | fixed in CROSS |
| should | "every gpt-5.5 miss" put the facade first: 23 of 24 did | fixed in CROSS |
| should | "$13.03 inside the $11 to $13 estimate": only the 60 valid runs ($12.92) are inside it | fixed in W20 |
| should | "the four wrong runs searched the longest of all": true only by median | fixed; replaced by the same-instance comparison (see inference SF6) |
| should | "no more work than a run that completed": the source says "than its same-instance comparator", and the comparison is of output | fixed in SUPERVISOR |
| notes | the row "calls before the first gold display" is a 1-based step, not a count of calls; 10 should be 10.5; 1e-6 should be 1.3e-6; 8 of 120 flagged records should be compared like for like (4 of 60 in Stage B); probe estimate $0.56; probe count note; W18's wmDiag "left running" claim contradicted by the lifecycle log; one quoted reason stretched to four runs | all fixed. The same off-by-one label was also fixed in the gpt-5 comparison table and script. W18 corrected, with an erratum |

## Inference lens: 3 must-fix, 9 should-fix, notes

The verifier's reading: ATTENUATED is the correct mechanical result, and in substance it cannot be told apart from ELIMINATED. The
decomposition is a defensible option, not an obligation, and leaving the model choice and the go/no-go decision to the supervisor
is right.

| Item | Finding | Resolution |
|---|---|---|
| MF1 | "the lie is ignored, not rejected" goes beyond what a keyword scan can show | now "not cited (0/60); whether it was read, used or discounted is not measured" |
| MF2 | calling gpt-5's held-out losses "operational, not attributional" contradicts the INCONCLUSIVE finding for 3 runs | fixed in CROSS |
| MF3 | "look exactly like gpt-5.5's 24" is false (6 CONVENTION_PRIOR, 1 ATTRIBUTION_FAILURE) | now "gpt-5.5's dominant failure (ENTRY_POINT_BIAS, 17 of 24)" |
| SF4 | the "at ceiling" decomposition argument covers only 1 of its 4 cells | reworded in all documents: 1 cell tested (15/15), 3 expected near ceiling but not measured |
| SF5 | the choice of model goes beyond the rule but was not marked as such | RESULTS now has a separate "Added interpretation (not preregistered)" section; SUPERVISOR says "my addition" |
| SF6 | the wrong-versus-correct comparison is confounded by cell | now uses the same-instance correct C11 runs (n = 6): 34.5 against 30.5 calls, ranges overlap |
| SF7 | lower reasoning tokens are read as less deliberation | now reported as a model-level offset; reasoning rises about a fifth against GPT-5.6's own 1-hop cells |
| SF8 | the Q1 and Q4 answers do not match the class | Q1: "lower, not established"; Q4: "largely; partial recovery under the rule" |
| SF9 | the harness interactions are said not to affect the other models, but this was never counted | reworded: gpt-5.5 used no login-shell test commands; stray braces were not counted for the other models |
| SF10 | "work" versus "output" | fixed in SUPERVISOR |
| SF11 | "no monotone ladder" asserts an absence | now "the shared data do not support a ladder claim" |
| SF12 | the Stage A consistency paragraph leaves out that gpt-5.5 also scored 0/5 and that the GPT-5.6 reference predates the frozen protocol | both added; the paragraph now says Stage A does not bear on the difference between the models |
| notes | the interval spans 0.90; the stall counted as a miss gives 25/30, still ATTENUATED; all contrasts rest on the same four misses; the odd hop was never blamed; more search is not more reading; the description of the decomposition is reconciled with the preregistration's "hop distance"; missing secondaries; weaker blinding; "most room to recover" | all added |
