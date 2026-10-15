Hi Hong Jin,

Update on the weaker-model direction, now with a result worth building on.

**Ladder.** Under the frozen protocol (same prompt, tools, 300 s budget, scoring), gpt-5.5 solved all 27 runs on the nine
held-out instances that GPT-5.6 had solved. gpt-5 answered only 17 of 27 within the budget: every miss was a timeout after it
had already found and read the faulty method, with no misranking, so it is operationally too slow at this budget rather than
a worse localizer. I stopped the ladder there rather than move to older models, since the thesis should be about a current
model.

**Stage A: the instances GPT-5.6 had missed, re-run unchanged on gpt-5.5.** Eight frozen instances plus the matched control
of the CHART pair, 32 valid runs.

- gpt-5.5 got **1 of 27** right on the eight breakers.
- The matched pair isolates the chain: same fault, same test, same failure values; the treatment arm differs from the
  control only in the 5-hop decomposition through two large existing classes. **gpt-5.5: treatment 0/5, control 5/5.** This
  matched the prediction recorded before the runs.
- Every one of the 26 misses is the failure we wanted: the gold's faulty line displayed, the method read in full, a test
  executed, and another method ranked first. No search failures, no timeouts.
- Blind labelling (two labellers per run, adjudicated) puts entry-point ranking first (12 of 26), then evidence-integration
  failures (6) and convention priors (5). gpt-5.5 is at or below GPT-5.6 on every instance and below it on three.

**What this means.** The same current model sits at ceiling on documented, single-owner instances and near zero on instances
that pair a long chain with a correct hop that looks locally wrong next to a quiet gold. The chain alone never moved accuracy
in any of our data; the chain plus that asymmetry does, on both GPT-5.6 and gpt-5.5.

**Your generator.** It is the same recipe as the copy I audited (two large hosts, anonymous insertion, facade narrative lie).
The lie has not been tested on GPT-5.x in combination with a chain: the September variants carried no lie, and the one real
generator run was solved. So I plan to use your machinery for Stage B and include the lie, with the asymmetry element added.

**Stage B proposal.** Fresh bugs in Lang, Math and a third project, each as a 2×2: chain (your recipe, with the lie) × odd
correct hop, 5 runs per cell on gpt-5.5, about $20. Golds pinned by evidence elsewhere in the repository (second caller,
passing test, distant geometry) but not restated locally, so an ownership audit cannot dissolve the result; the CHART
instance does not meet that bar, which is why I will not rest the claim on it alone.

Three choices for you: keep the lie inside the chain arm or make it a third factor (double the runs); gpt-5.5 at 300 s with
GPT-5.6 as reference, or re-run GPT-5.6 on the fresh pairs too; and the third project (your screener finds targets in Lang
and Math, none in JacksonCore; Chart outside the pie-plot classes would work).

Spend so far: about $29 in this phase, about $58 across both.

Best regards
