# Stage B ownership audit brief (one auditor per bug; the four cells of a bug share the fault and the trigger)

You are an independent auditor of ONE Stage B bug (four benchmark cells) for a fault-localization study. You did not build
it. Decide, from the code, its documentation and the tests alone, whether the declared gold method is the unique defensible
location of the fault in EVERY cell, and whether the four cells differ only in the declared factors.

    WM=/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/weaker-model-v1

## Inputs (read only these)

- `$WM/construction/stageB/specs/SB-<bug>-C00.json`, `-C01.json`, `-C10.json`, `-C11.json`: the four cell specs. Each declares the
  gold (class, method, file, fault edit), context edits, decoys, entry point, evidence, ownership reason, ownership tests, the
  trigger (an EXISTING test) and compensating edits. Treat every claim in them as a claim to check.
- `$WM/instances/SB-<bug>-C*/build/variant.patch`, `test.patch` (empty), `correct.patch`, and `validation.json`.
- `$WM/construction/stageB/BUILD_PROTOCOL.md` and `$WM/STAGE_B_PREREGISTRATION.md` (constraints the cells must meet).
- `$WM/construction/fresh/<Project>/`: the pristine checkout. READ-ONLY (it is a symlink to a shared fixture).

Do NOT read the design modules (`construction/stageB/designs/*.py`), model outputs, trajectories, metrics or reports
(`models/`, `analysis/`, `diagnostic/`, `review/`, `benchmark_runs/`, other `*.md`). Never open `.env` files.

## Method

1. For each cell: `S=$(mktemp -d /private/tmp/mxb-XXXXXX); cp -R $WM/construction/fresh/<Project>/ $S/w; chmod -R u+w $S/w`,
   then `git apply $WM/instances/<iid>/build/variant.patch` (test.patch is empty; the trigger already exists).
2. With `export PERL5LIB=$HOME/perl5/lib/perl5`: `defects4j compile`, `defects4j test -t <trigger>`.
3. Read every method on the trigger path in the variant (facade, every hop, the gold, the odd/plain sibling), with its javadoc,
   and the second production caller(s) named in `evidence`.
4. Try to break the gold:
   - (a) Is there a method other than the gold whose documented contract is violated on the trigger input?
   - (b) Does any non-gold method's javadoc contradict its own code, or is it loose enough that the observed behaviour is
     consistent with that method being at fault?
   - (c) Is there an equally small repair at a non-gold method, consistent with ALL documentation on the path and with the
     evidence methods, that passes the trigger AND the ownership tests? If you think one exists, apply it in your scratch copy
     and run the trigger and the ownership tests (`defects4j test -t ...` each). Classify every passing edit (AMENDMENTS W13):
     **competing repair** = it keeps every method on the trigger path used as its documentation describes (no hop's documented
     output becomes dead, no hop leaves the path); **bypass** = it replaces the gold's result with another implementation or makes a
     hop's output dead (for example recomputing the quantity from an unrelated existing method). Report `c_competing_repair` and
     `c_bypass` separately; only a competing repair rejects the bug; a bypass is recorded with its exact edit.
   - (d) Leakage: names, comments, the facade javadoc sentence, or added lines that point at the gold, at the odd hop, or read
     like a fault marker.
   - (e) Factor purity: C00 vs C01 differ only in the body of the sibling helper (plain vs odd form); C10 vs C11 only in the body
     of hop 3; the gold's text and fault are identical across the four cells; the gold is one call below the facade in C00/C01
     and five calls below it in C10/C11; the facade javadoc sentence (the lie) appears only in C10/C11. Report any other
     difference.
   - (f) Is the odd form (C01 sibling, C11 hop 3) actually correct for every input the tests exercise, and is its correctness
     pinned by something outside its own javadoc (a second caller, a passing test, the same idiom elsewhere)?
5. Delete your scratch directories.

## Verdict

Write `$WM/construction/stageB/audits/SB-<bug>.json`:

    {"bug": "...", "auditor": "independent agent", "verdict": "CONFIRMED" | "REJECTED",
     "per_cell": {"C00": {...}, "C01": {...}, "C10": {...}, "C11": {...}},
     "a_unique_contract_violation": true|false, "b_decoy_doc_issue": true|false, "c_competing_repair": true|false, "c_bypass": true|false,
     "d_leakage": true|false, "e_factor_purity": true|false, "f_odd_form_correct_and_pinned": true|false,
     "alternative_repairs_tried": [{"cell": ..., "method": ..., "edit": ..., "trigger_passes": ..., "ownership_tests_pass": ..., "doc_consistent": ...}],
     "reasons": "...", "notes": "..."}

CONFIRMED requires a = true, b = false, c_competing_repair = false, d = false, e = true and f = true for all four cells (a bypass
alone does not reject; it is recorded). If uncertain, REJECT
and explain. A rejected bug is rebuilt before any run, so a false CONFIRMED costs more than a false REJECTED.

Write only that audit file and your own `/private/tmp/mxb-*` scratch. No network, no model or API calls, no `git stash`, do
not kill processes you did not start, do not modify anything under `$WM` except the audit file.

## Final message

Under 120 words: the verdict and the decisive reason for each of (a) to (f).
