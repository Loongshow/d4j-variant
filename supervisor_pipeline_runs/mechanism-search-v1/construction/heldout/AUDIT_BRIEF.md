# Held-out gold audit brief (STABLE criterion 6)

You are an independent auditor of ONE held-out fault-localization benchmark instance. You did not build it. Decide, from the
code and its documentation alone, whether the declared gold method is the unique defensible location of the fault.

    MX=/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/mechanism-search-v1

## Inputs (read only these)

- `$MX/construction/heldout/<IID>.json`: the spec. It declares the gold, decoys, entry points, ownership reason, ownership
  tests, trigger and compensating edits.
- `$MX/instances/<IID>/build/variant.patch`, `test.patch` and `correct.patch`.
- `$MX/instances/<IID>/validation.json`: the gate record.
- `$MX/instances/<IID>/builder_report.json`. Treat the builder's claims as claims to check, not facts.
- `$MX/HELDOUT_CONFIRMATION_PLAN.md`: the common rules and the recipe for this instance.
- `$MX/construction/fresh/<Project>/`: the pristine checkout. It is READ-ONLY.

Do NOT read model outputs, trajectories, metrics or reports (`models/`, `analysis/`, `diagnostic/`, `review/`, `mining/`, other
`*.md`). Never open `.env` files.

## Method

1. Make a scratch copy with `S=$(mktemp -d /private/tmp/mxb-XXXXXX); cp -R $MX/construction/fresh/<Project> $S/w;
   chmod -R u+w $S/w`, then `git apply` both patches.
2. With `export PERL5LIB=$HOME/perl5/lib/perl5`, run `defects4j compile` and `defects4j test -t <trigger>`.
3. Read every method on the trigger path in the variant, with its javadoc.
4. Try to break the gold. Look for:
   - (a) A method other than the gold whose documented contract is violated on the trigger input.
   - (b) A non-gold method whose javadoc contradicts its own code, or is loose enough to allow the observed behaviour.
   - (c) An equally small repair at a non-gold method that is consistent with ALL documentation and passes the trigger and the
     ownership tests. If you think one exists, apply it in your scratch copy and run the trigger and the ownership tests.
   - (d) Leakage: names, comments, test names or vocabulary that point at the gold, or added lines that read like a fault
     marker.
   - (e) Whether the instance realises its recipe: the structural features the recipe requires are present, and its forbidden
     features are absent.
5. Delete your scratch directory.

## Verdict

Write `$MX/instances/<IID>/audit.json`:

    {"iid": ..., "auditor": "independent agent", "verdict": "CONFIRMED" | "REJECTED",
     "a_unique_contract_violation": true|false, "b_decoy_doc_issue": true|false, "c_alternative_repair": true|false,
     "d_leakage": true|false, "e_realises_recipe": true|false,
     "alternative_repairs_tried": [{"method": ..., "edit": ..., "trigger_passes": ..., "ownership_tests_pass": ..., "doc_consistent": ...}],
     "reasons": "...", "notes": "..."}

CONFIRMED requires a = true, b = false, c = false, d = false and e = true. If uncertain, REJECT and explain why. A rejected
instance is rebuilt before any run, so a false CONFIRMED costs more than a false REJECTED.

Write only `instances/<IID>/audit.json` and your own `/private/tmp/mxb-*` scratch. No network, no model or API calls, no
`git stash`, and do not kill processes you did not start.

## Final message

In under 100 words: the verdict and the decisive reason.
