# Stage B build protocol (working document; gates list to be completed from mechanism-search-v1's G0-G14)

Fixtures: `construction/fresh/{Lang,Math,Chart}` = this root's OWN fresh `defects4j checkout -p <P> -v 1f` trees (made 2026-10-14
after incident W12; byte-identical in tracked content to mechanism-search-v1's fixtures; real directories, never symlinks; read-only). Builders work in a scratch copy under `/private/tmp/d4j-stageB-<bug>-<cell>/`, created
with `cp -R` of the fixture, and emit unified diffs relative to the checkout root.

Known constraints (sources: STAGE_B_PREREGISTRATION.md, supervisor-recipe audit, memory notes):

- Generator facts: hosts are a seeded draw from files with >= 1500 newlines (`--min-host-lines`), target classes >= 1800
  lines; insertion anchor is chosen inside a host after both hosts are fixed; the fault is a one-line replacement in the
  terminal hop (`validate.apply_line_replacement`). Its LLM design step (`chain_design.py`, claude-opus-5) is NOT used here:
  the design (hop names, insertion anchors, lie sentence, original/buggy line) is hand-authored and recorded in
  `designs/<bug>.json` before any patch is cut.
- Chart sources are CRLF: edit byte-for-byte and capture patches in binary mode (`git diff --binary` or `diff` on untouched
  line endings); a patch that normalises line endings will not apply in the harness.
- Defects4J shells need `PERL5LIB=$HOME/perl5/lib/perl5`; use `/opt/miniconda3/bin/python`; macOS has no `timeout` binary
  (use `subprocess.run(timeout=)`). Full-suite timings: Lang ~20 s, Chart ~5 s, Math ~190 s (a Math full-suite validation
  takes 35-46 min; run Math validations in the background early).
- Names: hop and helper names must be neutral, in the host's vocabulary, and must not reuse names from earlier studies
  (`ring`, `rim`, `drift`, `nudge`, `shift`, `overlay`, `tally`, `computeCheckSum`, `intArrayToLong`, ...). No comment,
  name or lie sentence may mention the fault, the omitted step, or the gold/odd-hop role.
- Each cell is a separate variant directory with its own `variant.patch` (production code only), `test.patch` (empty or a
  trigger-test addition; identical across the four cells of a bug), `variant_manifest.json`, `validation.json`.
- Builders and auditors are different agents; the auditor receives only the patched tree and the trigger, not the design.

Directory use:
- `designs/`   hand-authored design per bug (facade, gold, omission, odd hop, hosts, anchors, lie sentence, pins, expected failure)
- `patches/`   cut patches per cell before packaging
- `validation/` compile / trigger / full-suite comparison records per cell
- `audits/`    independent ownership-counterfactual and pin audits per cell
- `logs/`      build logs

## Execution checklist (fixed 2026-10-14, before any validation result was known)

1. `stageB_validate.py construction/stageB/specs/<iid>.json` for the twelve cells (logs in `logs/validate_<iid>.log`); every cell
   must be `overall: READY`. A cell that fails is redesigned, not patched around; its three sibling cells are rebuilt with it.
2. One independent auditor per bug (AUDIT_BRIEF.md) writes `audits/SB-<bug>.json`; CONFIRMED on items (a) to (f) is required for
   all three bugs before anything is packaged. A REJECTED bug goes back to design.
3. `stageB_package.py construction/stageB/specs/<iid>.json` (twelve times) -> `new_bug_variants/<P>/bug-1/L20/CTV-*`; then
   `stageB_key.py` (merges into review/VARIANT_KEY.json; the eighteen Stage A entries stay).
4. `mx_plan.py plans/B_stageB_gpt55.json --iids <12 iids> --runs 5 --seed 1014 --purpose "Stage B 2x2, gpt-5.5"`: 60 slots, each
   round visits every cell once in a seeded random order.
5. `mx_freeze.py --add-plan plans/B_stageB_gpt55.json --server w55` (hashes variants, instance folders, key entries); then
   `mx_tmp_audit.py` must pass; then `ct_driver.py --server w55 --plan ... --verify-only` must discover all twelve variants.
6. `start_gpt_server.sh w55`, then `wm_run_chain.sh plans/B_stageB_gpt55.json` (caffeinate, health gate, stall and halt rules of the
   frozen driver). Cost cap $25. No other paid block runs concurrently.
7. `mx_metrics.py` -> `stageB_report.py` (cells, main effects, interaction, mechanical split); blind two-lens labelling of every miss
   with the Phase 7 set, cell identity hidden from the labellers; results into STAGE_B_RESULTS.md with the preregistered
   expectations quoted verbatim.
