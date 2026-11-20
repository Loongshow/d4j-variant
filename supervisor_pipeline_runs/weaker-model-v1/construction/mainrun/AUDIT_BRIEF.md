# Main run: ownership audit brief (one independent auditor per instance)

You independently audit ONE main-run instance of a fault-localisation study. You did not build it. Decide from the code, its
documentation and the tests alone whether the declared gold method is the unique defensible location of the fault, and whether
the instance follows the C10 recipe.

    WM=/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/weaker-model-v1
    export PERL5LIB=$HOME/perl5/lib/perl5; export PATH=/Users/shawnli/Desktop/Honours/defects4j/framework/bin:$PATH

## Inputs (read only these)

- `$WM/construction/mainrun/specs/MR-<key>.json`. It declares:
  - the gold (class, method, file, fault edit), the context edits, the decoys (the four non-gold hops) and the entry point;
  - the evidence, the ownership reason and the ownership tests;
  - the trigger (an EXISTING test) and the compensating edits.

  Treat every claim in it as a claim to check.
- `$WM/instances/MR-<key>/build/variant.patch`, `test.patch` (empty), `correct.patch` and `validation.json`.
- `$WM/construction/mainrun/BUILD_BRIEF.md`: the recipe the instance must meet.
- `$WM/construction/fresh-mr/<key>/`: the pristine checkout. It is READ-ONLY.

Do NOT read the design modules (`construction/mainrun/designs/`, `construction/stageB/designs/`). Do not read model outputs,
trajectories, metrics or reports (`models/`, `analysis/`, `diagnostic/`, `review/`, `benchmark_runs/`, `kpi-shift/`,
`stageB-gpt56/`, other `*.md`). Never open `.env` files.

## Method

1. Make a scratch copy and apply the variant patch:
   `S=$(mktemp -d /private/tmp/mxb-XXXXXX); cp -R $WM/construction/fresh-mr/<key>/ $S/w; chmod -R u+w $S/w; cd $S/w;`
   `git apply $WM/instances/MR-<key>/build/variant.patch`.
2. Run `defects4j compile` and `defects4j test -t <trigger>`.
3. Read every method on the trigger path in the variant, with its javadoc: the facade, each hop and the gold. Also read the evidence
   methods named in the spec.
4. Try to break the gold:
   - **(a) Unique contract violation.** Is there a method other than the gold whose documented contract is violated on the trigger
     input?
   - **(b) Hop documentation.** Does any non-gold hop's javadoc contradict its own code? Or is it loose enough that the observed
     behaviour is consistent with that hop being at fault?
   - **(c) Alternative repairs.** Is there an equally small repair at a non-gold method that passes the trigger AND the ownership
     tests, and is consistent with ALL documentation on the path and with the evidence methods?
     - If you think one exists, apply it in your scratch copy, run the trigger and the ownership tests, and then run the full suite
       with `defects4j test`.
     - Classify every passing edit:
       - **competing repair**: it keeps every method on the trigger path used as documented;
       - **bypass**: it replaces the gold's result with another implementation, or makes a hop's output dead.
     - Only a competing repair rejects the instance. Record a bypass with its exact edit.
   - **(d) Leakage.** Do names, comments or added lines point at the gold or read like a fault marker? Does the facade's javadoc
     sentence (the lie) name the fault or the omitted step?
   - **(e) Recipe conformity.**
     - The gold is exactly five calls below the facade.
     - The five hops are in five different existing classes.
     - The facade body is a guard plus one delegating call.
     - The facade javadoc carries one added procedural sentence that the code does not do.
     - The gold's own javadoc does not state the omitted step.
     - The trigger is an existing test, and only it newly fails.
   - **(f) External pin.** Is the gold's convention pinned outside its own javadoc, by evidence code or a passing test?
5. Delete your scratch directories.

## Verdict

Write `$WM/construction/mainrun/audits/MR-<key>.json`:

    {"instance": "<key>", "auditor": "independent agent", "verdict": "CONFIRMED" | "REJECTED" | "FLAG_AMBIGUOUS",
     "a_unique_contract_violation": true|false, "b_hop_doc_issue": true|false, "c_competing_repair": true|false, "c_bypass": true|false,
     "d_leakage": true|false, "e_recipe_conformity": true|false, "f_external_pin": true|false,
     "alternative_repairs_tried": [{"method": ..., "edit": ..., "trigger_passes": ..., "ownership_tests_pass": ..., "full_suite_clean": ..., "doc_consistent": ..., "class": "competing|bypass|fails"}],
     "path": ["facade ...", "hop1 ...", "...", "gold ..."], "reasons": "...", "notes": "..."}

**CONFIRMED** requires a = true, b = false, c_competing_repair = false, d = false, e = true and f = true.

**FLAG_AMBIGUOUS**: the instance is valid as built, but ownership is genuinely arguable. An example is a hop that a careful
engineer could reasonably call the fault location. Flagged instances are run but reported separately, never counted silently.

**REJECTED**: anything else. If uncertain between CONFIRMED and REJECTED, choose REJECTED and explain.

Write only that audit file and your own `/private/tmp/mxb-*` scratch. No network, and no model or API calls. No `git stash`. Do not
kill processes you did not start. Do not modify anything under `$WM` except the audit file.

## Final message

Under 120 words: the verdict and the decisive reason for each of (a) to (f).
