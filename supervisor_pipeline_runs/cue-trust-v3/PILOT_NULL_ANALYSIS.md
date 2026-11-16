# Null pilot analysis: GPT-5.6 cue-trust pilot

The pre-registered null-pilot rule (amendment A1) applies:
- no contrast on any instance is STRONG;
- all six are NULL, with delta 0;
- Acc@1 is 1.00 in every cell over 27 valid runs.

So the work stops here. No forced-inspection follow-up runs and no main block starts. This file diagnoses the null and proposes
one minimal redesigned pilot.

Evidence:
- `GPT56_*` reports and `analysis/gpt56_tables_F0.md`;
- three independent per-instance diagnoses (`analysis/gpt56_review_labels_and_diagnoses.json`);
- five blind hand labels, which agree with the metrics on 50/50 fields.

## Diagnosis by candidate cause

| Candidate cause | Verdict | Evidence |
|---|---|---|
| Names and comments were not exposed | **No** | The cue was shown at its location in 17/18 cue runs. Every run read the full gold and decoy bodies. |
| Baseline at ceiling or floor | **Partly; part of the phenomenon** | Neutral Acc@1 was 1.00, so a gold-excusing cue could only lower it, and it never did. Neutral decoy-first was 0, so a decoy-blaming cue had the full range, and it never rose. The ceiling reflects the task, not a measurement problem. |
| Cue strength insufficient | **Yes, but confounded with task ease** | Each cue is refuted by evidence shown in the same window, or by the failing test source in the prompt (details below). The test source and the self-convicting faults acquit the decoys whatever the cue, so the pilot cannot separate weak cues from an easy task. |
| Decoy implausible | **Mixed** | CT-CHART-03's decoy is plausible on the symptom (the observed 0.0 is computed inside it), but reading it refutes it. CT-CHART-01's decoy is cleared by arithmetic on the test's own constructor arguments. CT-LANG-01's decoy is acquitted by deduction from a guard assertion inside the trigger test. |
| Manipulation simply ineffective | **Not yet decidable** | No cue as built presented a story that survives one screen of reading. The pilot cannot tell "identifier cues cannot move GPT-5.6" from "these cues were self-refuting". |

### How the cues refuted themselves

**Comments placed beside the faulty line did not help the cue.**
- On CT-LANG-01 and CT-CHART-03 the gold-excusing comments sit just above the faulty line.
- On CT-LANG-01, 2 of 3 CG runs cited the false comment as further evidence against the gold.
- On CT-CHART-03 no evidence chain engaged the comments, whose false local claims `Math.max`, 30 lines below, refutes.
- These are hint comments, which the pre-registered calibration rule already says not to use for strengthening.

**Field renames are refuted by co-visible, consistent uses.**
- On CT-CHART-01 and CT-CHART-03 the decoy-blaming renames swap or rename private fields.
- Each field is also read and written by an adjacent getter, setter, constructor, javadoc or `equals`, shown in the same
  80 to 120 line window, and these uses agree with the true behaviour.
- One CT-CHART-03 wording also predicts a different failure value (0.2 instead of the observed 0.0), which `failing_tests` refutes.

**The prompt's failing test source acquits the decoys.**
- *CT-CHART-01:* the decoy's ranges follow from the test's literal arguments by simple arithmetic. That check appears in 8 of 9
  evidence chains. The decoy body was displayed before the cue in 2 of 6 cue runs; in decoy-blaming runs the cue sits in the
  decoy file itself.
- *CT-LANG-01:* the trigger contains an owner-invariance guard, `split(input, "")` returning the input unsplit, which exercises
  the same decoy path and acquits it. All 9 evidence chains used it.

**The faults convict themselves locally:**
- a single `!`;
- `maximum = 0` beside `minimum = +INFINITY`;
- a forwarded `separator` that contradicts the condition three lines above.

**GPT-5.6 verified rather than took shortcuts.** It ran the trigger test at step 1 or 2 in every run and read full bodies before
submitting. Runs displayed 674 to 2,572 lines of files with 2,181 to 7,357 lines, navigating by grep and line ranges. The pilot
has no contrast that could show whether file size affected reading.

## Minimal redesigned pilot (v2), proposed and not run

Same protocol:
- GPT-5.6;
- `reasoning_effort: medium`;
- the frozen F0 prompt;
- the same budgets and harness.

Same three instances, conditions and size: CT-CHART-01, CT-LANG-01 and CT-CHART-03 × {C0, CG, CD} × 3 = 27 runs, about USD 5.

The cue construction changes under four rules, with new variant IDs and full re-validation. Rule 3 also extends the decoy sets,
and CT-LANG-01's trigger test changes (below). Both fall outside the pre-registered calibration lever, so the v2 pilot needs its
own dated amendment.

1. **Literal-reading coherence.** For every cue level, read the cue literally and write down what it predicts. It must:
   - blame a registered decoy;
   - reproduce the observed failure signature exactly;
   - survive the first window an agent displays around the decoy, and arithmetic on the trigger test's literal arguments.

   A level that fails is rejected before validation.
2. **Identifier cues only, placed before the gold and away from the fault.** This is the pre-registered calibration lever:
   names that make correct code look wrong.
   - No cue comments.
   - The neutral C0 comment must not state facts that convict the gold, as CT-LANG-01's current neutral comment does.
   - Place renames where the agent reads first: decoy-method locals and parameters, and facade parameters for a gold-excusing
     cue. Never on or next to the faulty line.
3. **Register every executed method a cue implicates.** For example, add CT-CHART-01's decoy constructor as a decoy. Re-run the
   G6 and G9 gates.
4. **Self-refutation screen.** Reject a rename whose every use is co-visible and consistent within one 80 to 120 line window,
   such as a field together with its getter, setter and `equals`.

For CT-LANG-01, also move the owner-invariance guard out of the trigger test into a separate test. G9 would then check owner
invariance against the full suite, not the trigger alone. This is the only instance-level change, and the true fault stays
visible.

**Pre-commitment.** Use the same A1 contrasts and classes.
- *A STRONG contrast on any instance:* proceed per A1 to the forced-inspection test on that instance.
- *Null again:* conclude that on these three instances, under this protocol (runnable trigger test, test source in the prompt),
  the identifier cues tested did not override code-level evidence for GPT-5.6, and that no shortcut-taking was observed. Then
  change the research question instead of adding more cue variants. Options are conditions where verification is costly, or the postponed
  lower-baseline models.

**Not proposed.** These would also likely move accuracy, but they change the frozen protocol and break comparability with the
earlier GPT-5.6 data, so they are not "minimal":
- removing the test source from the prompt;
- cutting budgets.
