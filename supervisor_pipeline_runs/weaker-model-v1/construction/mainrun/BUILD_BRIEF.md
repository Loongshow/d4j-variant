# Main run: builder brief (one builder per Defects4J bug identity)

You build ONE benchmark instance for a fault-localisation study. The instance transfers the verified Stage B **C10** recipe to the
fixed checkout of a real Defects4J bug (for example `Lang-3`). The fault you inject is synthetic. The instance is tied to the real
bug through its checkout and, where possible, through its target class.

    WM=/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/weaker-model-v1
    export PERL5LIB=$HOME/perl5/lib/perl5; export PATH=/Users/shawnli/Desktop/Honours/defects4j/framework/bin:$PATH
    PY=/opt/miniconda3/bin/python

## The recipe (C10, unchanged from Stage B)

- **Facade.** An EXISTING public static method that an existing test calls. Prefer a candidate listed for your instance, in the class the
  real Defects4J bug modified. Its body becomes an argument guard (if the original had one) plus ONE delegating call to hop 1.
  The recipe's `rewrite_facade` appends the **lie**: one procedural sentence in the facade's own documentation voice. It describes
  an algorithm the code does not perform, like the Stage B lies, which give a plausible but wrong description of how the method
  works. It must not mention the fault, the omitted step or any hop.
- **Five hops.** These are new `public static` methods, one in each of the five host classes that the recipe draws for your instance.
  Run `$PY $WM/scripts/mr_lib.py preview <key> <target file relative to the source root>` and use the hosts in draw order: hop i
  goes into drawn host i, and hop 5, the gold, goes into host 5.
  - The recipe inserts each hop at a seeded anonymous point. You only supply the method text.
  - The original facade's computation is redistributed along the chain:
    - plumbing and aggregation sit in hops 1-4, for example a fold, a pass-through, or a placement step;
    - the per-element core of the computation sits in hop 5, the gold.
  - Each hop has house-style javadoc and a neutral name in its host's vocabulary.
  - A host may be unusable: a static method there will not compile, or it cannot see a needed type. In that case preview with
    `n=6` and take the next drawn host. Record why in `host_notes`. Never choose hosts by hand for convenience.
- **Fault.** A one-line omission inside the gold, in an iteration or decision whose effect no caller can pre-filter or recover. The
  gold's javadoc states the idiomatic contract and is silent on the omitted step (a "quiet" gold), yet the omission violates that
  contract on the trigger input.
- **No local trace: a HARD rule from batch 3 on** (AMENDMENTS W29). The WHOLE gold, as it reads in the variant, must pass every
  item of `$WM/construction/mainrun/NO_LOCAL_TRACE_CHECKLIST.md`. Read it completely before designing.

  Summary only; the checklist's text governs:
  - T1: every parameter's value can still change the result. It must not be unused, read only after being overwritten, read only to
    compute dead locals, or used only in an argument check.
  - T2: no local is dead; none is frozen; and no branch, case or ternary is dead. Frozen means a literal that is never reassigned,
    or a variable the loop is meant to move that is never assigned in it: a cursor, write position, counter, flag or best-so-far.
    A bound, length or offset computed before the loop is not frozen.
  - T3: no member of a closed set (closed only as the checklist's closure rule defines) is left out while a sibling gets the
    treatment. No class named in the gold's own text may be handled only in part. Pair halves and range ends always count.
    Not T3: no member of the set handled at all, or exactly one member of an unnamed set of three or more, such as a NaN-only skip
    in a sum. Float and double special values form a set only if the gold names the class (for example "finite").
  - T4: no phrase in the gold's javadoc, comments or identifiers names a concrete rule, limit, bound, value class, case or property
    that the body visibly does not meet. Caller preconditions on parameters, such as "null not permitted", are not T4.

  Before choosing the omission, apply the checklist to the CORRECT gold as well, and rewrite any pattern it already shows. Record an
  item-by-item self-check (T1-T4: absent, one line each) in the design docstring and in your result.
- **Pre-run checks and the single redesign (batch 3).** An independent auditor (`AUDIT_BRIEF.md`) and an independent trace checker
  (`TRACE_CHECK_BRIEF.md`) check your READY instance. If the audit is REJECTED or the checker returns TRACE, you get their reasons
  together and ONE redesign, before any run. A REJECTED audit was also sent back once in batches 1 and 2 (`MAIN_RUN_PLAN.md`).
  - A new auditor and a new checker then check the redesigned version.
  - Before changing anything, archive version 1: copy your design, spec, `instances/MR-<key>/validation.json`, the audit file and the
    trace verdict into `construction/mainrun/history/<key>/v1/`.
  - Never mention the earlier findings in the design text, spec, code or comments. The new auditor and checker must not be able to
    see that there was a first version.
  - If no valid fault without a local trace exists for your target, report UNBUILDABLE and say why.
- **Facade choice (batch 3 on).** Your facade MUST be one of your instance's allowed targets in your batch's pre-registration (`main-run/BATCH3_PREREGISTRATION.md` or `main-run/BATCH4_PREREGISTRATION.md`).
  This overrides "Prefer a candidate" above. If none of them can carry the recipe, the instance is UNBUILDABLE.
- *(Batch 2 only, superseded by the rule above from batch 3 on.)* **Fault type preference** (AMENDMENTS W26). Among valid faults, prefer an omitted **special-case step** after
  which the gold still reads as a complete, ordinary routine for ordinary input. Examples:
  - a special-value skip, such as a NaN skip in a sum;
  - a pairing check, such as a surrogate-pair low-half check;
  - a state reset, such as a word flag reset at whitespace;
  - a boundary or delimiter rule.

  The step the specification requires is documented outside the gold, in the facade javadoc or a test. Avoid omissions that leave a
  **visibly broken idiom** in the gold:
  - a loop index or write position that never advances;
  - an argmax or argmin that never records its index;
  - a result variable that is never assigned or is returned null on the ordinary path;
  - a bound that the gold's own javadoc states.

  This is a preference among valid designs. Every validity rule above and below still applies unchanged: the quiet gold, the
  single owner, a single trigger and the external pins.
- **Trigger.** An EXISTING test method (empty test.patch) that fails deterministically on the variant. It must be the ONLY test in
  the full suite that newly fails (gate G5). Pick a fault that exactly one existing test catches.
- **External pins.** The gold's convention must be pinned outside the gold's own javadoc: by other production code doing the same
  step (a sibling overload, another caller) and by passing tests. List them in `evidence` (2-4 `Class::method`) and in
  `ownership_tests` (passing tests that pin the convention).
- **Single owner** (AMENDMENTS W13). No one-line edit at a non-gold hop may pass the trigger and the full suite while staying
  consistent with every hop's documentation. Declare 2-3 plausible alternative repairs at hops in `compensating.chain`. Gate G9
  checks that none of them absorbs the fault. A bypass that throws away the gold's output is allowed, but you must record it.

## How to work

1. Read the C10 parts (`chain`, `gold`, `trigger`, `evidence`, `ownership_*`, `compensating.chain`) of the Stage B designs
   `$WM/construction/stageB/designs/B1_lang.py`, `B3_chart.py` and `B4_math.py`. Ignore `one_hop` and `odd`. Read
   `$WM/scripts/mr_spec.py`, which shows exactly what the design keys do.
2. Create the fixture with `$PY $WM/scripts/mr_lib.py fixture <key>` (it prints the source and test roots), and get the seed with
   `$PY $WM/scripts/mr_lib.py seed <key>`.
3. Study the target, its tests and its callers in `$WM/construction/fresh-mr/<key>`. This directory is READ-ONLY: never edit it.
   Work only in your own `/private/tmp/` scratch copies.
4. Write `$WM/construction/mainrun/designs/<key>.py` with a module docstring that explains the design and a
   `DESIGN = {...}` dict. Required keys:
   - identity: `instance` (`"<key>"`), `project`, `bug_id` (int), `seed` (the instance seed), `src_root`, `test_root`;
   - `facade {file, class, method, near_line}`;
   - `trigger {existing: True, test_file, test_class, test_method}`, `expected_signature` (a substring of the failure message);
   - `gold {method, text, fault {old, new}}`, where `old` and `new` are exact multi-line text from the gold body;
   - `chain {facade_body, lie, hops: [5 x {file, class, method, imports, text}; the 5th is {..., gold: True}]}`;
   - `evidence`, `ownership_reason`, `ownership_tests`, `compensating {chain: [...]}`, `host_notes`;
   - optional `pre_edits {chain: [...]}`, only for behaviour-preserving edits the chain needs, as in B3's guard rewrite.
5. Run `$PY $WM/scripts/mr_spec.py $WM/construction/mainrun/designs/<key>.py C10 --check`. The trigger must fail with your expected
   signature.
6. Run `$PY $WM/scripts/mr_validate.py $WM/construction/mainrun/specs/MR-<key>.json > $WM/construction/mainrun/logs/validate_MR-<key>.log 2>&1`.
   Every gate must pass (`overall: READY`). If a gate fails, fix the DESIGN and re-run steps 5 and 6. Up to 4 redesigns; Math
   validations take 20-40 minutes.
7. If the recipe cannot be applied without making the design semantically invalid, stop and report UNBUILDABLE with the reason.
   Examples: no target whose computation can be split into a chain, no fault that only one test catches, or a gold that cannot be
   made the unique owner. Do not force it.

## Rules

- **Allowed writes.** Write ONLY `construction/mainrun/designs/<key>.py`, `construction/mainrun/logs/*<key>*`, `construction/mainrun/history/<key>/` (batch-3 redesign archive), what `mr_spec.py` and
  `mr_validate.py` write for your instance (`construction/mainrun/specs/MR-<key>.json`, `instances/MR-<key>/`), the fixture that
  `mr_lib.py fixture` creates, and your own `/private/tmp/` scratch.
- **Off-limits.** Never edit `construction/fresh*`, `scripts/`, `models/`, `review/`, `plans/`, `FREEZE.json`, `new_bug_variants/`,
  or another instance's files.
- **No answers.** Do not read model outputs, trajectories or results: `models/*/benchmark_runs`, `analysis/`, `diagnostic/`,
  `stageB-gpt56/`, `gpt5-timeouts/`, `kpi-shift/`, or the report files.
- **Safety.** No network, and no model or API calls. Never open `.env` files. No `git stash`. Do not kill processes you did not
  start.
- **Names and text.** No added line, name or comment may contain fault vocabulary (bug, fault, wrong, incorrect, broken, fix,
  todo, ...). Do not reuse earlier study names: ring, rim, drift, nudge, shift, overlay, tally, signedSums, placeTotals,
  collectValues, categoryLimits, extentOfCategories, isAnyOf, memberAt, classifyAt, lookupAt, firstIndexOutside, tabulate,
  mostFrequent.
- **Test sources.** Tests are never edited. The trigger already exists.

## Final message (structured)

Return:
- `status`: READY, UNBUILDABLE or FAILED;
- the instance key;
- the facade, the gold, the trigger, and the fault in one line;
- the gate summary;
- the number of redesigns;
- the hosts used, with any host notes;
- any concern a reviewer should check: possible alternative owners, bypasses, or a lie that could be read as true.
