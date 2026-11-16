# mechanism-search-v1: pre-registration

Written 2026-10-10, before any run in this root. Later changes are appended as dated amendments and never edited in place. This
file is hashed by the freeze, and the driver refuses paid calls if it changes.

## Question

Which controlled, interpretable task properties make a strong repository-level LLM fault-localization agent rank a wrong method
above the true faulty method? The primary interest is accuracy (Acc@1, MRR), especially the pattern "gold exposed, gold code
inspected, wrong method still ranked first". Search cost is secondary.

## Protocol (identical to the completed GPT-5.6 cue pilot; only the benchmark instance changes)

- **Model and profile:** `gpt-5.6` with the canonical profile `mini-swe-agent-openai-gpt-5-6`. `reasoning_effort: medium`,
  passed explicitly. OpenAI Responses API through litellm 1.98.0, mini-swe-agent 2.4.6.
- **Prompt and budgets:** the frozen localization-only prompt (base sha256 `845e21e7…`), F0 arm only; 50 model calls, a 300 s
  timeout, and a 5-test budget recorded but not enforced.
- **Server code:** byte-identical to the pilot's (tree sha `1e1b6fa9…`): P1 external workspace, P2 F1 switch (off), P3
  explicit effort, P4 agent environment allowlist. The launcher gives the server an allowlisted environment.
- **Driver and gates:** freeze verification before every paid call, the per-slot ledger, workspace-isolation, protocol-identity,
  integrity and leakage checks, and contamination scanning.
- **Run status:** the uniform provider-failure rule (`scripts/ct_status.py`, rules 1 to 3 plus the A2 and A3 corrections).
  Behavioural outcomes are counted (intention to treat) and never re-run. An infrastructure failure may be replaced once per
  slot. After a second infrastructure failure on a slot the block halts. One top-up of that slot after the planned block is
  allowed only after a written halt review shows the failures were provider-side (stall replay), and at most two top-ups per
  cell.

## Evidence tiers

1. **Exploratory: mechanism discovery and screening.** This covers:
   - re-hosted earlier validated variants (built and tuned against Claude in earlier roots, never run on GPT-5.6);
   - new screening prototypes, 3 valid runs per instance;
   - any revision made after a behavioural result.

   No exploratory result is reported as confirmation.
2. **Confirmatory: held-out.** For the strongest 2 to 4 mechanisms, the mechanism recipe is frozen in writing first. Then NEW
   instances are built that were never used in tuning: 3 fresh bugs per mechanism across at least 2 projects, 5 valid runs each.
   Held-out instances are never modified after their first behavioural run.

**Provenance:** `INSTANCE_PROVENANCE.csv` records, for every instance, its mechanism, prototype, revision, parent, tier and
screening result.

## Screening classes (3 valid runs per instance)

- **PROMISING** if any of the following holds:
  - (A) Acc@1 ≤ 1/3;
  - (B) the gold was exposed in at least 2 runs AND misranked in at least 2;
  - (C) the same wrong method was ranked above the gold in at least 2 of 3 runs.
- **WEAK** if exactly 1 of 3 runs mislocalizes and none of A to C holds.
- **NULL** if 3 of 3 rank the gold first.

A mechanism family is PROMISING if any of its instances is.

## Stable accuracy reduction (held-out)

A mechanism is STABLE only if all six hold:
1. pooled held-out Acc@1 ≤ 0.60;
2. at least 2 of 3 fresh instances have Acc@1 ≤ 0.60 individually;
3. failures are not dominated by provider errors or no-answers: no-answers are under half of the misses;
4. at least half of the wrong answered runs exposed the gold method;
5. no answer leakage and no invalid or ambiguous gold: the scanner is clean and the validity gates pass;
6. an independent audit, an agent that did not build the instance, confirms each gold is behaviourally defensible.

Preferred: pooled held-out Acc@1 ≤ 0.50. Mechanisms are labelled SUPPORTED (stable), PARTIALLY_SUPPORTED (some held-out reduction
but not all six criteria) or NOT_SUPPORTED.

## Global stop rule

Stop the search when either holds:
- **A:** at least two distinct mechanisms are STABLE;
- **B:** at least 12 mechanism families have been screened and held-out confirmation is complete for the strongest at least 3
  families, but none reaches pooled held-out Acc@1 ≤ 0.60. The result is then that GPT-5.6 is robust under the tested manipulations.

## Validity gates for every new instance (`scripts/mx_validate.py`)

- the variant compiles;
- the trigger fails deterministically (3 times, byte-identical) with the expected signature;
- the fixed (gold-repaired) version passes the trigger and the full suite;
- collateral is acceptable: the full suite fails only on the trigger;
- reproduction from a fresh checkout;
- the gold method is objectively defined, as the minimal repair;
- no test-method name contains a gold or decoy method name;
- no fault vocabulary in the added lines;
- every decoy is proven correct: unchanged, or changed only by behaviour-preserving context edits under which the CORRECT
  configuration passes the full suite;
- owner invariance: no declared one-line decoy edit absorbs the fault;
- ownership mechanisms carry an executable or auditable reason why the gold owns the bug.

Re-hosted variants keep their original validation and must reproduce in this harness (apply, compile, trigger fails with the
recorded signature).

## Measures (`scripts/mx_metrics.py`, definitions frozen in its docstring)

- **Outcome:** gold rank, Acc@1, reciprocal rank, rank-1 category (GOLD, DECOY, ENTRY_POINT, OTHER, NO_ANSWER).
- **Exposure and inspection:** gold exposed (fault line displayed), gold fully read, decoy exposed and fully read, external
  evidence displayed.
- **Execution:** test run, failure values seen, independent probe.
- **Cost and effort:** tool calls, model calls, tokens (including reasoning), cost, wall time.
- **Failure mode:** every wrong run gets a Phase 7 label (`FAILURE_MODE_ANALYSIS.md`): SEARCH_FAILURE, DISCOVERY_WITHOUT_INSPECTION,
  ATTRIBUTION_FAILURE, EVIDENCE_RETRIEVAL_FAILURE, EVIDENCE_INTEGRATION_FAILURE, CONVENTION_PRIOR, LOCAL_ODDNESS_BIAS,
  ENTRY_POINT_BIAS, LEXICAL_SHORTCUT, OTHER.

## Cost discipline

- Screening cells have 3 runs and held-out cells 5.
- No main benchmark before a mechanism survives held-out confirmation.
- No Anthropic runs before a STABLE GPT-5.6 mechanism exists.
- `COST_LEDGER.csv` is kept per block, family, instance and mechanism.
- The user is asked before any stage that would substantially exceed this staged design, roughly above USD 60 cumulative.
