# Main run: the Stage B method on real Defects4J bug identities (gpt-5.5)

Plan written 2026-10-16, after Hong Jin's decisions of the same day. This file comes before any construction or paid run of this
phase, and changes to it are logged in `../AMENDMENTS.md`.

## Objective and KPI

Maximise the number of Defects4J bug instances for which at least one gpt-5.5 run ranks the gold method below first. The KPI is a
count to maximise: there is no baseline, no decomposition and no statistical test at this stage.

- **Run-level.** `SHIFT` means the run submitted a ranking and the gold is not first (gold rank > 1, or the gold is absent from the
  top 10). Timeouts and other no-answer runs are reported separately. They are never counted as shifts.
- **Instance-level.** `INSTANCE_SUCCESS` means at least one of the instance's runs is a `SHIFT`.
- **Headline.** "N validated instances tested; M with at least one shift". The total of shifted runs over answered runs, and
  per-project counts, are reported alongside.
- **Flagged instances.** If the auditor flags an instance as having genuinely ambiguous ownership (`FLAG_AMBIGUOUS`), it is run and
  reported separately, and is never counted in M.

## Instance definition and provenance

An instance is a real Defects4J bug identity, `<Project>-<bugId>` (for example `Lang-22`). The fault is synthetic and is injected
into that bug's fixed checkout. Each instance records:

- the project and the bug id;
- the fixed revision and the harness checkout;
- the fixture: `construction/fresh-mr/<key>`, a real-directory copy of the harness's own `<key>/fixed`;
- the real bug's modified classes;
- the target class and method, which are taken from the real bug's modified class where possible;
- the injected fault;
- the gold method;
- the transformation: the hosts and anchors with their seed, and the lie.

All of this is in `INSTANCE_PROVENANCE.csv`, the spec (`construction/mainrun/specs/MR-<key>.json`) and the variant manifest
(`new_bug_variants/<P>/bug-<id>/L20/<CTV>`).

## The recipe transferred: Stage B C10, unchanged

C10 is chosen over C11 because it is simpler and equally strong on gpt-5.5. Under the KPI, gpt-5.5 shifted the gold on 3 of 3 bugs
in both cells, in 12 of 15 C10 runs and 11 of 15 C11 runs. The odd hop added nothing.

- **Facade.** An existing public static method that the trigger test calls. Its body becomes a guard plus one delegating call. The
  recipe's `rewrite_facade` appends a procedural sentence (the lie) to its javadoc.
- **Five hops.** These are new public static methods in five existing classes of at least 1500 lines.
  - The hosts are drawn by the supervisor recipe's seeded `pick_two_hosts`, repeated, with public classes only (W15). Each hop is
    inserted at the recipe's seeded anonymous interior anchor.
  - The seed is deterministic per instance (`mr_lib.seed`) and is fixed before the build, so nobody chooses hosts by hand.
  - Hop 5 is the gold. The original computation is redistributed along the chain: plumbing in hops 1 to 4, the per-element core in
    the gold.
- **Fault.** A one-line omission in the gold. It is quiet: the gold's javadoc does not state the omitted step. Its convention is
  pinned externally by evidence code and passing ownership tests.
- **Trigger.** An existing test, which is the only test that newly fails. The test patch is empty.
- **Validity.** The single-owner rule of W13 applies: a bypass is allowed and recorded, but a competing repair rejects the instance.
- **Protocol** (identical to Stage B on gpt-5.5):
  - frozen server w55 (tree `b62f0a2f…`), `gpt-5.5` at `reasoning_effort: medium`;
  - base prompt sha `845e21e7…`;
  - 50 tool calls, 5 test runs, 300 s;
  - external workspace, leakage scanner, freeze verification before every paid call;
  - frozen `ct_driver.py`, health gate, stall rules, one replacement per slot;
  - scored with the frozen `mx_metrics.py`.

New scripts (none of them guarded) are copies of the Stage B builders that work from a per-instance fixture:

- `mr_lib.py`, `mr_spec.py`, `mr_validate.py`, `mr_harness_check.py`, `mr_package.py`, `mr_key.py`;
- `mr_candidate_pool.py`.

No guarded script or server file changes. The frozen driver, scanner, freeze library and metrics already support any bug id: the
freeze library reads `bug_id` from the key, and the scanner reads `fresh` from the key.

## Candidate pool (`DEFECTS4J_CANDIDATE_POOL.csv`)

`mr_candidate_pool.py` reads all 854 active bugs at their fixed revisions and applies these rules:

- **Hosts.** At least 5 public classes of at least 1500 lines.
- **Target.** A public static method in the bug's modified classes that passes the recipe's candidate filter (4 to 50 lines, not a
  pure delegate, self-containedness > 0) and is called by at least one test.
- **Excluded projects.** Projects with full suites of about 1000 s (Time, Collections, JacksonDatabind, Mockito) are excluded,
  because validation runs the full suite several times.

Result: **91 eligible** (Lang 41, Closure 25, Math 17, JacksonCore 6, Chart 2) and 763 rejected:

| Rejection reason (a bug can have several) | Bugs |
|---|---|
| no static self-contained method in the modified classes | 607 |
| fewer than 5 host classes | 371 |
| slow full suite | 202 |
| no test calls the candidate | 39 |

Eligible bugs are ranked by fit with the recipe. The ranking uses suite speed, host count, the candidate's self-containedness,
tested candidates, an existing harness checkout and a single-file real fix.

## Batches

Batch 1 has 8 instances. All have an existing harness checkout, so no change to the shared workspace store is needed. Their target
methods are distinct, and none is a target used earlier in Stage B.

| Instance | Pool rank | Target class (allowed targets) |
|---|---|---|
| Chart-2 | 1 | DatasetUtilities (not findStackedRangeBounds, Stage B's) |
| Lang-22 | 2 | Fraction (getReducedFraction / getFraction) |
| Lang-39 | 6 | StringUtils (repeat / abbreviate) |
| Lang-45 | 10 | WordUtils (abbreviate / initials / capitalize) |
| Lang-1 | 12 | NumberUtils (createBigInteger / createBigDecimal) |
| Lang-14 | 9 | StringUtils (containsNone / substring / containsAny) |
| Lang-16 | 18 | NumberUtils (min / max array forms) |
| Math-3 | 44 | MathArrays (convolve / normalizeArray) |

The batch then runs through these steps:

1. **Build.** One builder agent per instance follows `construction/mainrun/BUILD_BRIEF.md` and writes the design. `mr_spec.py`
   builds the spec, and `mr_validate.py` runs the 16 Stage B gates; the instance must be READY.
2. **Audit.** One independent auditor agent per instance follows `construction/mainrun/AUDIT_BRIEF.md` and returns CONFIRMED,
   FLAG_AMBIGUOUS or REJECTED. A REJECTED instance goes back to design once; if it fails again, it is logged as UNBUILDABLE.
3. **Package and plan.** `mr_package.py`, then `mr_key.py`, then `mx_plan.py`, with 5 runs per instance in seeded rounds.
4. **Freeze and run.** `mx_freeze.py --add-plan`, then the tmp audit, the driver's `--verify-only` check and
   `start_gpt_server.sh w55`, then `wm_run_chain.sh`.
5. **Score.** `mx_metrics.py` then the main-run report, which writes `MAIN_RUN_RESULTS.csv`, `SHIFTED_INSTANCES.md` and
   `FAILED_TO_TRANSFER.md`.

**Decision after batch 1.** If the method transfers (most validated instances shift), batch 2 takes the next 10 to 15 by pool rank,
with distinct targets; new harness checkouts are made as needed. If it transfers poorly, the cause is diagnosed before more
instances are built. Completed instances are never redesigned after their results are seen.

## Cost control

| Item | Estimate |
|---|---|
| gpt-5.5 runs | median $0.429 and mean $0.431 per run (Stage B chain cells), so about $2.16 per instance (5 runs) |
| Batch 1 runs | 40 runs, about $17.2; with health probes (about $0.008 each) and roughly 5% replacements, about **$18–19** |
| Construction | no OpenAI spend: builders and auditors are agents of this session |

Construction time is the limit on throughput, so agent time per instance is tracked. Recorded spend before this phase is $64.10, so
batch 1 brings the total to about $83. Before each later batch its cost is estimated. If projected cumulative spend materially
exceeds the discussed range, the work stops and is reported.

## Outputs

- **Plan and construction:** `MAIN_RUN_PLAN.md`, `DEFECTS4J_CANDIDATE_POOL.csv`, `INSTANCE_BUILD_LOG.csv`,
  `INSTANCE_PROVENANCE.csv`.
- **Results:** `MAIN_RUN_RESULTS.csv`, `SHIFTED_INSTANCES.md`, `FAILED_TO_TRANSFER.md`.
- **Cost and reporting:** `COST_LEDGER.csv` (this phase's rows; the root ledger is updated as well), `SUPERVISOR_PROGRESS_UPDATE.md`.
