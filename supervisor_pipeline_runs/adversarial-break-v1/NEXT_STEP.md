# Next step

The brief says not to optimise further after the maximum-difficulty experiment, so this file records the one experiment the
results point to and why, and what not to do.

## Recommended: the pinned-definer attribution pair (clean, within-pair, both arms identical except the owner of the sign)

`ADV-DEFINER-01` is the only attack that broke every model, and its clean core is already a thesis-grade design. Turn it into a
matched pair on the CHART-PIE-03 base:

- **CONTROL (gold = definer).** `PlotUtilities.drift` computes the wrong sign; `Plot.nudge` applies the negation correctly.
  `PlotUtilitiesTests.testDrift` exists in both arms and asserts the intended convention, so under CONTROL it fails alongside the
  trigger (declared collateral) and under TREATMENT it passes.
- **TREATMENT (gold = adapter).** `drift` is correct and pinned by the same passing test; `nudge` lacks the negation. This is
  `ADV-DEFINER-01` with the pin moved into the base so that it is not variant-only.
- Same chain, same trigger, same expected values, same method names and javadocs. The only difference is which of two methods
  owns the sign. Predicted from this root: CONTROL Acc@1 near 1.0 on every model; TREATMENT near 0.0 on Opus and Sonnet.
- Runs: Sonnet x10 per arm, Opus x5 per arm, GPT-5.6 x5 per arm when credits are available (the frozen GPT-5.6 server must be
  restarted by the owner first; see `anthropic-pilot-v1/diagnostic/INCIDENT_frozen_server_process.md`). One paid slot per
  server, three fast probes before each block, no result-based early stop.
- Pre-register: gold, roles, the collateral test, and the reading that a TREATMENT miss with `drift` at rank 1 is
  OWNERSHIP_MISATTRIBUTION. Measure Acc@1, MRR, gold rank, whether the agent opened the pinning test, and whether it ran it.

This turns the strongest adversarial finding into a causal statement about one lever with no planted decoys, no coarsened
assertions and no variant-only evidence.

## Secondary (mechanism check, not a benchmark instance)

Re-run the TREATMENT arm with one added sentence in the task prompt: "before attributing a convention error, check whether a
unit test fixes that convention". If Acc@1 recovers, the failure is a search-policy gap (the models never look for pinning
contracts), not a reasoning gap. This is a protocol change and must be run as a separate labelled protocol, never mixed with
the frozen `v2` results.

## Harness fixes before any further Claude block (found in this root, see `diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`)

- Export `PERL5LIB=$HOME/perl5/lib/perl5` in every Claude server launcher so `defects4j test` executes for the agent as it did for the
  frozen GPT-5.6 server. `scripts/start_model_server_tests.sh` already does this; the pilot launcher does not.
- Give the model client a request timeout of about 120 s with one retry (litellm's default is 600 s): every one of the nine hung requests
  in this root would then have been retried inside the 300 s budget instead of killing the run.
- Re-state comparability with GPT-5.6 only after both fixes: the pilot's NEAR_EQUIVALENT verdict holds for prompt, budgets, parser and
  repository access, not for test execution.

## Do not

- Do not tune the composite further; its extra manipulations were inert on Opus and the brief closes optimisation here.
- Do not carry `ADV-LEX-01`, `ADV-REGISTRY-01`, `ADV-OVERLOAD-01` or `ADV-OWNER-01` into the thesis benchmark as attacks: the
  first rests on a planted decoy and does not transfer to the stronger model; the other three did not break the weaker models.
- Do not count Haiku exhaustion as attack effect; its plain-control exhaustion rate is the baseline.
- Do not rerun or modify any completed run in this root, the pilot root, or the frozen GPT-5.6 root.

## What this recommendation rests on

Definer attribution with a non-terminal gold produced Acc@1 0.0 to 0.2 on Opus across fifteen runs in three protocols (v2, composite,
v2+runner) and 0.0 on Sonnet across twenty valid attempts (core plus composite); every hit came from reading the definer's unit test;
the mirror-image design with the gold in the producer was solved every time; and the composite showed that stacking artifacts on the
lever changes exhaustion, not attribution. The pair above isolates that one lever with nothing else in play.
