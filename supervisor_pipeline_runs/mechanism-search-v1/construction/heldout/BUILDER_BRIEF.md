# Held-out builder brief (one builder per instance)

You are an independent builder of ONE held-out benchmark instance for a fault-localization study. The study root is

    MX=/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/mechanism-search-v1

You are given an instance id (IID), a recipe (HA, HB or HC) and a Defects4J project. You build a single-fault variant of that
project's `bug-1` fixed version that realises the recipe, then validate and package it with the existing deterministic tools.

## Read these, and only these, from the study root

- `HELDOUT_CONFIRMATION_PLAN.md`: the "Rules common to all recipes" section, and your recipe's section. Follow them exactly.
- `scripts/mx_build_validate.py`: the docstring gives the spec format and gates G0 to G13. Read the code if a gate fails.
- `instances/NEW-R5-M7/spec.json` and `instances/NEW-R5-M7/builder_report.json`: an example of the spec and report format
  only. That instance belongs to a different recipe.
- `construction/USED_METHODS.txt`: methods you must NOT use as the gold, a decoy, an entry point or a helper host.
- `construction/fresh/<Project>/`: the pristine checkout. It is READ-ONLY; never modify it.

**Do NOT read anything else in the study root.** In particular, never read `models/`, `analysis/`, `diagnostic/`, `review/`,
`mining/`, `plans/`, any `*.md` report other than the plan, other instances' folders, or any model output, trajectory or
metric. You must build from the recipe alone, without seeing how any model behaved. Never open `.env` files.

## How to work

1. **Shell and scratch.**
   - `export PERL5LIB=$HOME/perl5/lib/perl5`. Defects4J commands are `defects4j compile` and `defects4j test [-t Class::method]`,
     run inside a checkout copy.
   - Make your scratch copy with `S=$(mktemp -d /private/tmp/mxb-XXXXXX); cp -R $MX/construction/fresh/<Project> $S/w;
     chmod -R u+w $S/w`. Never put the IID, the recipe name or role words such as "gold" in any path under `/private/tmp`.
   - Delete your own scratch directories when you finish.
2. **Design the instance.**
   - Choose an entry point and a computation in the project that fit your recipe. They must not appear in
     `construction/USED_METHODS.txt`.
   - Implement the helper chain as behaviour-preserving context edits (`context_edits`), then the single fault (`gold.edits`).
   - Write the javadoc of every helper precisely. The gold's javadoc must state the property its code then violates. Every
     other method on the path must satisfy its own javadoc exactly.
   - Add a neutral trigger test, at least one ownership test (passing on the variant) and at least two natural one-line
     compensating edits at non-gold methods (`compensating`).
   - Check by hand in your scratch copy:
     - the CORRECT configuration (context edits plus tests, no fault) passes the full suite;
     - the variant fails only the trigger, with a deterministic signature.
   - Run at most one full test suite at a time. Other builders share the machine.
3. **Write the spec.** Path: `$MX/construction/heldout/<IID>.json`, in the format of the example. Set:
   - `"iid": "<IID>"`, `"group": "<IID>"`, `"recipe": "<HA|HB|HC>"`;
   - `"tier": "HELDOUT"`, `"kind": "new"`;
   - `"mechanism"` and `"tags"` as given to you;
   - `"project"`, `"src_root"`, `"test_root"`.
4. **Validate.** Run from `$MX`:

       /opt/miniconda3/bin/python scripts/mx_build_validate.py construction/heldout/<IID>.json 2>&1 | tee instances/<IID>/validate.log

   You need `"overall": "READY"` in `instances/<IID>/validation.json`, with every gate passing. You may run the validator at
   most twice per design. If the design still fails, abandon that location and design a fresh one (at most two designs). If
   neither reaches READY, stop and report FAILED.
5. **Package** (only when READY): `/opt/miniconda3/bin/python scripts/mx_package_new.py construction/heldout/<IID>.json`. Do
   NOT run `mx_rebuild_key.py` and do not edit `review/`; the coordinator does that.
6. **Report.** Write `$MX/instances/<IID>/builder_report.json` in the example's format, with these fields:
   - `iid`, `recipe`, `status`, `project`, `mechanism_fit`;
   - `gold`, `decoys`, `entry_points`, `evidence`;
   - `ownership_reason`, `trigger`, `expected_signature`, `fault_lines`;
   - `gates_failed`, `construction_notes`, `concerns`.

   Be candid in `concerns`. Record anything an auditor could use to argue that a non-gold method is an equally valid fault
   location.

## Hard limits

- Write only these:
  - `$MX/construction/heldout/<IID>.json`;
  - `$MX/instances/<IID>/` (the validator and packager write here too);
  - the variant folder that `mx_package_new.py` creates;
  - your own `/private/tmp/mxb-*` scratch, which you delete at the end.
- No network access, no model or API calls, no servers. Never print or read credentials.
- No `git stash`. Do not kill processes you did not start. Do not touch other builders' files.
- No fault vocabulary in any added line or name: bug, fault, wrong, incorrect, broken, fix, inverted, reversed, etc. (see
  FORBID in the validator).

## Final message

In under 150 words: status (READY and packaged, or FAILED), the variant id printed by the packager, the gold `Class::method`,
and your top concern.
