# cue-trust-v3 (NON-CANONICAL RESEARCH BENCHMARK)

Do misleading identifier names and comments change which method a repository-level LLM fault-localization agent blames, when the
code's behaviour is unchanged? Design: `/Users/shawnli/Desktop/Honours/thesis_writeup/EXPERIMENT_REDESIGN_v3.md`.
Pre-registration (frozen before any run): `PREREGISTRATION.md`.

Location note: this tree lives in the session worktree (`.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/`)
because the base checkout is protected from edits by this session. It READS shared resources from the base checkout
(`workspaces/defects4j` checkouts, `variant-lab/node_modules`, `supervisor_pipeline_runs/.env`, the OCFLB helper library) and never
writes there. The frozen servers, canonical variants and earlier experiment trees are untouched.

## Layout

| Path | Contents |
|---|---|
| `scripts/ct_lib.py` | deterministic builder: spec -> variant.patch / test.patch for C0, CG1, CG2, CD1, CD2 and CORRECT |
| `scripts/ct_validate.py` | gates G0-G10 + X (behaviour identity by `javap -c -p`, owner invariance, collateral, fresh reproduction) |
| `scripts/ct_package.py` | installs READY instances under opaque IDs; private key in `review/VARIANT_KEY.json` |
| `scripts/setup_server.py`, `start_server.sh`, `stop_server.sh` | patched server COPIES: external workspaces (P1), inspection-prompt switch (P2) |
| `scripts/ct_plan.py`, `ct_driver.py` | randomised interleaved plan; one-slot driver with health gate, identity/integrity/leak checks, credit halt |
| `scripts/scan_v3.py` | out-of-workspace and cross-variant leakage scan |
| `scripts/ct_metrics.py` | per-run measures and per-cell summary |
| `instances/<ID>/` | spec.json, build/, validation.json |
| `new_bug_variants/` | installed variants (CTV-xxxxxx) |
| `models/<server>/` | server roots (sonnetF0, sonnetF1, opusF0, opusF1; diagF1 is diagnostics only) |
| `workspace_archive/` | agent workspaces moved here after each run |
| `diagnostic/` | server and driver logs, probes, block logs |

## Commands

```
export PERL5LIB=$HOME/perl5/lib/perl5
python scripts/ct_lib.py instances/<ID>/spec.json        # build
python scripts/ct_validate.py instances/<ID>/spec.json   # validate (READY required)
python scripts/ct_package.py instances/<ID>/spec.json    # install
zsh scripts/start_server.sh sonnetF0                     # start a server (reads the authorized env file; never prints it)
python scripts/ct_plan.py plans/pilot.json --instances A,B,C --levels C0,CG,CD --runs 3
python scripts/ct_driver.py --server sonnetF0 --plan plans/pilot.json
python scripts/ct_metrics.py
zsh scripts/stop_server.sh sonnetF0
```

Status notes are appended below as the work proceeds.

### 2026-10-08 status: built and validated; pilot halted on the provider credit error

**Instances (all READY, 36/36 gates, installed under opaque IDs):**

| Instance | Gold method | File size | Depth | Decoy | CD lever |
|---|---|---|---|---|---|
| CT-CHART-01 | `XYPlot::getDataRange` | 6,028 lines | deep (~86 lines) | `XYDataImageAnnotation::getXRange/getYRange` | private field swap x/y, w/h |
| CT-LANG-01 | `StringUtils::splitByWholeSeparatorWorker` | 7,356 lines | shallow (15 lines) | 4-arg `StringUtils::splitWorker` | parameter rename |
| CT-CHART-02 | `XYPlot::render` | 6,028 lines | deep by header offset (41 lines) | `RendererUtilities::findLiveItemsLowerBound` | local renames low/high |
| CT-CHART-03 | `DatasetUtilities::iterateToFindDomainBounds` | 2,180 lines | shallow (13 lines) | `NumberAxis::autoAdjustRange`, `getAutoRangeIncludesZero` | private field swap / inversion |

Pilot plan `plans/pilot.json`: CT-CHART-01, CT-LANG-01, CT-CHART-03 x {C0, CG, CD} x F0 x 3 = 27 slots (seed 20261008).
CT-CHART-02 is held back for the main block: its decoy carries an original comment that contradicts its return value at every
level, C0 included, which leaves little headroom for a CD effect.

**Halt.** `ct_driver.py --server sonnetF0 --plan plans/pilot.json` started 22:23:54Z. The first two health-gate probes timed out at
90 s. The finished smoke run `smoke-20261007T222355213Z` shows `anthropic/claude-sonnet-4-6` failing with litellm BadRequestError
"credit balance is too low" after 9 retries (backoff 4-60 s, about 250 s in total), cost 0. Driver stopped by PID at 22:29:17Z and
logged as HALT_PROVIDER_CREDIT. **No benchmark run was launched; zero pilot data exist.** `ct_metrics.py` has nothing to score.

**Driver fix.** mini-swe-agent retries a provider 400, so a credit refusal first looks like a probe hang. `probe()` now scans the
finished smoke runs started by this driver for the credit message and halts with HALT_PROVIDER_CREDIT (pre-patch copy:
`diagnostic/ct_driver.pre_smokescan.py`). Tested offline against the real smoke run.

**Resume (superseded by the GPT-5.6-first sequence below; Sonnet/Opus are postponed).** Top up the Anthropic balance, then:

    zsh scripts/start_server.sh sonnetF0
    python scripts/ct_driver.py --server sonnetF0 --plan plans/pilot.json
    python scripts/ct_metrics.py

Then apply the pre-registered pilot gate and calibration rule (a cue that moves Acc@1 by < 1/3 is strengthened along the name-body
lever, re-validated, and given new variant IDs), build fresh main-block instances, and run F0 and F1.

### 2026-10-08 status: switched to GPT-5.6-first; BLOCKED_OPENAI_CREDENTIAL

The user moved the pilot to `mini-swe-agent-openai-gpt-5-6` first and postponed Sonnet and Opus. Phase 0 found no authorized
OpenAI credential. The authorized env file holds only `ANTHROPIC_API_KEY`. The tool shell has no `D4J_OPENAI_API_KEY` or
`OPENAI_API_KEY`. No user-started GPT server is listening. No GPT server copy was created and no run was made.

To unblock, the server process needs `D4J_OPENAI_API_KEY` (or `OPENAI_API_KEY`) with OpenAI credit; the account ran out on
2026-09-25. `D4J_OPENAI_MODEL=gpt-5.6` is set by the launcher. Reasoning effort must also be pinned: earlier GPT-5.6 runs passed
only `drop_params: true` in `model_kwargs`, so they used the provider default and never recorded the effort value.

### 2026-10-08 status: GPT-5.6 harness ready; waiting for the OpenAI credential

Amendments A1 (GPT-5.6-first pilot), A2 and A3 (corrections from two adversarial readiness reviews) are in `PREREGISTRATION.md`.

| Item | State |
|---|---|
| GPT server roots | gptF0 (pilot, F0), gptF1 (Phase 3 only), gptDiag (one paid smoke run), gptStub and gptStubF1 (free stand-in) |
| Patches | P1 external workspace, P2 F1 switch, P3 explicit reasoning effort, P4 agent environment allowlist |
| Model | `gpt-5.6` via the canonical profile `mini-swe-agent-openai-gpt-5-6`, reasoning effort `medium`, explicit |
| Free harness proof | passed: final stand-in proofs A to E (valid, integrity stop, contamination stop, credit halt then replacement, orphan adoption) |
| Freeze | `FREEZE_GPT56_PILOT.json`, written before the first paid call and verified by the driver |
| Credential | not yet present (BLOCKED_OPENAI_CREDENTIAL) |

Sequence once the key is available, either exported in your own terminal or added as `D4J_OPENAI_API_KEY` to the authorized
env file:

    zsh scripts/start_gpt_server.sh gptDiag
    python scripts/ct_driver.py --server gptDiag --plan plans/smoke_gpt.json       # ONE bounded paid smoke run (not counted)
    # check the Phase 1 items on that run -> diagnostic/PHASE1_ACCEPTANCE.json
    zsh scripts/start_gpt_server.sh gptF0
    python scripts/ct_driver.py --server gptF0 --plan plans/pilot.json             # 27 runs, F0
    python scripts/ct_metrics.py && python scripts/gpt56_tables.py

### 2026-10-09 status: GPT-5.6 pilot complete; NULL; stopped under the pre-registered rule

| Item | Result |
|---|---|
| Smoke run | 1 paid run on gptDiag; all ten Phase 1 items passed |
| Pilot | 27 valid runs on gptF0 (F0, `gpt-5.6`, effort `medium`) |
| Accuracy | gold ranked first in 27/27; Acc@1 = MRR = 1.00 in every cell |
| Contrasts | all six NULL |
| Exclusions | 2 provider stalls on slot 8; replays 5 to 14 s; block continued by the frozen `plans/pilot_cont.json` under the uniform rule (`diagnostic/HALT_REVIEW_slot8.md`) |
| Gate | cue shown in 17/18 cue runs; at most USD 0.32 per run; 0 timeouts; hand labels agree with the metrics on 50/50 fields |
| Spend | about USD 5.21 in total |

The forced-inspection follow-up was not triggered, and no main block was started.

Reports:
- `GPT56_PILOT_RESULTS.md`
- `GPT56_CUE_EFFECTS.md`
- `GPT56_TRAJECTORY_ANALYSIS.md`
- `GPT56_REASONING_USAGE.md`
- `GPT56_RUN_LEVEL_RESULTS.csv`
- `PILOT_NULL_ANALYSIS.md`, which holds the diagnosis and the minimal v2 proposal, not run.

The OpenAI key was pasted into the chat transcript on 2026-10-09; rotate it.
