# GPT-5.6 pilot: reasoning-token use (observational)

Reasoning effort was fixed at `medium` before the block and passed explicitly in every request. Reasoning tokens were not
manipulated. As pre-registered, low token use is never read as "laziness" on its own.

## Distribution

Each cell gives min, median and max over valid runs.

| Condition | n | Reasoning tokens per run | Reasoning tokens per model call | Output tokens per run | Model calls |
|---|---|---|---|---|---|
| C0 | 9 | 450, 744, 1,166 | 56, 124, 233 | 2,481, 3,055, 3,272 | 5, 6, 8 |
| CG | 9 | 528, 736, 1,211 | 54, 105, 242 | 2,455, 2,845, 4,472 | 5, 6, 10 |
| CD | 9 | 632, 774, 1,570 | 74, 136, 194 | 2,295, 3,042, 5,411 | 4, 7, 14 |
| All | 27 | 450, 749, 1,570 | 54, 124, 242 | not tabulated | not tabulated |

**Median reasoning tokens by instance:**

| Instance | C0 | CG | CD |
|---|---|---|---|
| CT-CHART-01 | 717 | 545 | 755 |
| CT-LANG-01 | 1,056 | 915 | 856 |
| CT-CHART-03 | 639 | 633 | 742 |

## Reading

- **Outcome.** Every valid run ranked the gold first, so reasoning use cannot be compared across outcomes. All 27 runs sit in
  the GOLD row.
- **Per run.** Reasoning per run is small and stable, 450 to 1,570 tokens, which is about 124 tokens per model call. It is in
  line with the earlier GPT-5.6 families, whose medians were 477 to 743 with no effort sent; OpenAI documents medium as the
  default.
- **By condition.** There is no consistent condition effect. The CD cell has the widest range. Its largest run (1,570 tokens)
  is a CT-CHART-03 decoy-blaming run with 14 model calls and an independent probe. The longest search (36 tool calls) used 742
  tokens.
- **Failure values.** Runs that displayed the failure values used somewhat more reasoning (median 856) than runs that did not
  (717). These are descriptive only.
- **Stalls.** Neither excluded stall reflects long reasoning. Replays of both stalled states answered in 5 to 14 s with 24 to 509
  reasoning tokens (`diagnostic/HALT_REVIEW_slot8.md`).

Low reasoning use did not coincide with shortcuts: every run read the full gold and decoy bodies and ran the trigger test. At
medium effort, GPT-5.6's evidence gathering happens in its tool use, not in long hidden deliberation.
