# Batch 6 (cell C10f) addendum to the builder brief

You build a **C10f** instance. `BUILD_BRIEF.md` applies in full, with its "batch 3" rules (the no-local-trace HARD rule, the pre-run
checks and the single redesign, the redesign archive) and with `main-run/BATCH6_PREREGISTRATION.md` as your batch's pre-registration.
C10f is the C10 recipe with one change: **where the fixed revision has fewer than five public classes of at least 1500 lines other than
the facade's class, the five hosts are the five largest public classes.** Everything else is unchanged: the facade, the five static hops
with hop 5 as the gold, the quiet one-line omission, the facade lie, an existing trigger test that newly fails alone, the 16 gates, the
audit and the trace check.

## 1. Hosts

Your task record in `main-run/batch6_tasks.json` carries `host_mode`:

- `host_mode = "1500"`: at least five other public classes reach 1500 lines. Draw the hosts exactly as before, with
  `$PY $WM/scripts/mr_lib.py preview <key> <facade_rel> 5` (the recipe's seeded draw over classes of at least 1500 lines). Nothing changes.
- `host_mode = "largest5"`: fewer than five such classes exist. Your hosts are the five files listed in `host_files_top5` of your task
  record (the five largest public, non-interface, non-enum classes other than the facade's class, by newline count; ties by path), in
  that order: hop 1 in the first, ..., hop 5 (the gold) in the fifth. Use the recipe's anchor picker for the insertion point in each
  (`mr_lib.py preview` prints anchors for a given host list only in the 1500 regime; for `largest5` call
  `stageB_lib.pick_insertion_anchor` on each listed file with the instance seed, as `stageB_spec.py` does, and record the anchors in
  `host_notes`). If a listed host cannot carry a static method (it is an interface in disguise, an enum, or a class whose file does not
  compile with an added static method), say so in `host_notes`, skip to the next-largest public class, and record the substitution; do not
  choose a host by any other criterion.
- Record in the design docstring: `host_mode`, each host's newline count, and the smallest host's size. These are covariates of the
  analysis.

## 2. Reachability probe before designing (new, mandatory)

The pool's test-caller check is static. Before designing, confirm that an existing test really reaches your facade:

1. in a scratch copy of the fixture, make the facade's first statement `throw new IllegalStateException("PROBE-REACHED");`
2. compile and run the facade's candidate trigger tests (`defects4j test -t <TestClass>::<method>`) or, if cheap, the full suite;
3. the facade is usable only if at least one existing test fails with that message. Record the probe (tests run, result) in the design
   docstring under `reachability_probe`.

If no existing test reaches any allowed facade, report UNBUILDABLE with the probe result (brief step 7), as JacksonDatabind-37's
builder did in batch 5.

## 3. Spec generation

Run `$PY $WM/scripts/mr2_spec.py $WM/construction/mainrun/designs/<key>.py C10 --check` instead of `mr_spec.py`. `mr2_spec.py` is a copy
whose only change is the cell label (`mechanism MAIN_RUN_C10F`, `tier MAIN_RUN_C10F`), so that the frozen metrics and the main-run report
keep C10f instances apart from the C10 instances. Validation, packaging and the key are unchanged (`mr_validate.py`, `mr_package.py`,
`mr_key.py`).

## 4. Facade reuse

If your task record has `facade_reuse_of`, the same method is the facade of another instance. That is allowed and recorded in batches 5
and 6, and changes nothing in how you build.

## 5. What to return

The structured result of `BUILD_BRIEF.md`, plus `host_mode`, the five host sizes and the reachability probe result.
