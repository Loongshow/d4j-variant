# Minimum causal explanation

**Statement.** Both models attribute an under-determined sign/scale fault to the hop whose body looks wrong for what that hop is
supposed to be. The adversarial pair placed the wrong-looking body (`drift` returning `point1 - point2`, an inward vector under a name
that reads outward) at the CORRECT hop and made the faulty hop an omission that looks like a faithful scale-and-forward; the models blamed
the definer. OCFLB placed the wrong-looking body at the FAULTY hop in both arms (an explicit `-drift`, `high << 1`, `low - top`, `* top`,
`agreeing > 1`, `(memberLength % 2) == 0` against a javadoc and a name that say otherwise) and made the correct hop conventional; the models blamed the faulty hop. The
effect disappeared primarily because OCFLB made the faulty hop locally self-incriminating (explicit operator or constant, 9/10 pairs) and
secondarily because it documented the convention at H2 (10/10 pairs), which gave Sonnet a second local cue. The pin test (there is no production second caller in either benchmark) was not
necessary and was read in only one decision across both benchmarks, the single adversarial hit (Opus v2+runner run-005).

## Ranked explanations

1. **Self-incriminating faulty hop (local salience at the gold).** Strongest. Opus solved OCFLB-Chart-01's adapter arm 4/5 with neither
   the `drift` nor the `nudge` javadoc ever in view, citing the visible negation (the one miss read `-drift*pct` as the usual definition and
   blamed the consumer hop `rim`, still above the definer); it failed the adversarial adapter 0/5 in the v2 block with the same kind of
   information in view, citing the definer's operand order. Graders: OCFLB adapter fault is a visible operator/constant in 9/10 pairs and the owner is inferable
   from a single read of the faulty hop without its javadoc in 7/10; adversarial: 0 and no. Predicted counterfactual: V5 (obvious
   operator, vague docs) restores accuracy for both models.
2. **Explicit local contract (H2 javadoc states the convention in 10/10 OCFLB pairs; H3 javadoc states the transformation in 9/10,
   Lang-04 excepted).** Correlated for Sonnet (quoted in 8 of 24 Chart rationales), absent from Opus's adapter-arm decisions; its causal
   status is untested by the existing runs: Sonnet was correct in 20/20 answered adapter-arm runs in which the H2 javadoc text never
   appeared in any output (35/35 across both arms) and Opus in 24/25 with it in view in none, so it is not necessary, and whether it is
   sufficient rests on the V3/V4 prediction. In the three adversarial Opus runs that did have the `drift` javadoc in view, two still
   blamed `drift` (one citing the javadoc), so vague documentation does not exonerate a definer whose body looks reversed. Predicted counterfactual: V3/V4 restore Sonnet (0.67-1.0), only partly Opus.
3. **Conventional-looking correct hop.** The flip side of 1: in OCFLB the correct hop (`point2 - point1` for a "drift", plain sums,
   plain shifts) reads naturally, so nothing competes with the faulty hop for suspicion. In the adversarial pair the correct definer's
   unconventional order competed and won. This is what made the adversarial case an attack rather than a hard instance.
4. **Under-specified documentation in the adversarial pair.** Presumed necessary for 3 to bite (whether a documented inward convention
   exonerates `drift` is untested; V3 tests it, and the one related observation, Opus v2+runner run-004 with the `drift` javadoc in view and
   `drift` still blamed, does not support it) but not sufficient on its own: with a conventional-looking definer and an omission at the adapter,
   under-specification would leave the models with no local cue at all (Level A ambiguity), which is a different failure.
5. **Second-caller pinning.** Not causal. Present in both benchmarks, read in almost none of the decisions, and the only adversarial hit
   came from reading it. It makes ownership unique for the validator, not for the model.
6. **Test runner, prompt, budgets, names, files, chain shape, trigger, failure text, candidate count.** Not causal: identical or shown
   irrelevant (runner fixed in v2+runner: adversarial effect unchanged).

## The one-sentence version

The earlier effect required the odd-looking line to sit at the correct hop and the faulty hop to be an omission; OCFLB reversed both,
so the same heuristic that produced the misattribution now produces the right answer, and the pin that was meant to carry the
ownership evidence was never part of either decision.

## What this predicts for the counterfactual pilot (pre-registered)

V5 restores both models (CASE C). V3 and V4 restore Sonnet and partly Opus (CASE B for Sonnet). V1 and V2 do not restore either
(rejecting CASE A and CASE D). A rival that needs neither names nor javadocs (trace the sign numerically, then blame the hop that
holds the only explicit sign-determining token: a subtraction whose operand order can flip, or a unary minus) predicts the same
V0/V5/V6 outcomes and additionally that V3 and V4 restore neither model; V3 on Sonnet is therefore the decisive condition, and three V0
anchor runs per model in the same session close the model-version confound (the two benchmarks ran 48 h apart on undated aliases). If V3/V4 restore Opus as well, documentation is a sufficient cue for both and the solution must remove
it (Level B rule 2); if only V5 does, the solution must additionally keep adapter faults as omissions (rule 3). Either way the design in
`SOLUTION_DESIGN.md` applies; the pilot decides how strictly rule 2 must be enforced.
