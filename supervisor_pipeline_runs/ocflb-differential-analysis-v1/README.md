# OCFLB differential analysis v1

Question: why did the adversarial definer pair (`adversarial-break-v1/ADV-DEFINER-01`: Sonnet 0/7, Opus 0/5) reduce accuracy while OCFLB v1
(10 pairs; Sonnet 80/80 answered runs correct, Opus 49/50) did not?

Answer in one line: the models blame the hop whose body looks wrong for its name/doc; the adversarial pair put the odd-looking line at
the correct hop and made the faulty hop an omission; OCFLB put the odd-looking line (explicit operator/constant, or a body contradicting an
explicit javadoc) at the faulty hop in both arms. The second-caller pin was present in both and read in almost none of the decisions.

| File | Content |
|---|---|
| `ADVERSARIAL_VS_OCFLB_DIFFERENCE_MATRIX.md` | 38 model-visible factors, labelled LIKELY/POSSIBLY/UNLIKELY causal |
| `TRAJECTORY_DIFFERENTIAL.md` (+ `analysis/trajectory_differential.json`, `analysis/trajectory_table.md`) | observable behaviour of 17 answered adversarial runs vs 24 answered OCFLB runs |
| `analysis/LOCAL_CUE_GRADING.md` (+ `analysis/local_cue_grading.json`) | independent graders over the real patches of all ten OCFLB pairs and the adversarial pair |
| `analysis/patch_salience.json` | mechanical salience markers of every arm's bug line |
| `HYPOTHESIS_EVALUATION.md` | H1-H8 verdicts with evidence |
| `MINIMUM_CAUSAL_EXPLANATION.md` | ranked explanation and pre-registered pilot predictions |
| `WHY_OCFLB_BECAME_EASY.md` | the plain account |
| `COUNTERFACTUAL_DESIGN.md`, `COUNTERFACTUAL_RESULTS.md` | V1-V5 on the adversarial pair: validated and installed (`counterfactuals/packages/`, `new_bug_variants/`); pilot BLOCKED_PROVIDER_QUOTA, `scripts/run_pilot.sh` runs it |
| `SOLUTION_DESIGN.md` | externally pinned / locally under-specified principle, five rules, Level A/B/C |
| `NEXT_LARGE_BENCHMARK_SPEC.md` | OCFLB v2 spec, ten answers |
| `TIME_CRITICAL_SCALE_PLAN.md` | FAST / MEDIUM / FULL |
| `FINAL_RECOMMENDATION.md` | thesis recommendation |
| `analysis/critique.json` | three adversarial reviews of the causal explanation |
| `scripts/` | `build_counterfactuals.py`, `validate_cf.py`, `install_cf.py`, `start_server.sh`, `cf_driver.py`, `probe_model.py`, `run_pilot.sh`, `cf_metrics.py`, `build_cf_results.py` |
