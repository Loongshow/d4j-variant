# Protocol deviation: the Claude agents could not run `defects4j test` (found 2026-09-27 07:15Z)

**Evidence.**
- In every run of this root, and in the Claude pilot (`anthropic-pilot-v1`), the tool output of any `defects4j test ...` command is
  `Can't locate String/Interpolate.pm in @INC ...` returned in about 0.1 s. Example: `models/sonnet46/.../ADV-MASK-01/run-004`,
  `models/opus55/.../ADV-COMPOSITE-01/run-001`, pilot `CHART-PIE-TREATMENT-03/run-002`.
- In the frozen GPT-5.6 root (`diagnostic-noncanonical-v3/benchmark_runs/mini-swe-agent-openai-gpt-5-6`), 64 of 64 scanned runs
  that issued `defects4j test` got `Running ant (compile.tests) ... OK / Running ant (run.dev.tests) ... OK / Failing tests: ...`.
- Cause: the Claude servers (pilot and this root) were started by launchers that pin the provider environment but do not export
  `PERL5LIB=$HOME/perl5/lib/perl5`; the running `sonnet46` server process has no `PERL5LIB` in its environment. The frozen
  GPT-5.6 server had been started from a shell that had it. The agent inherits the server's environment.

**What it means.** The protocol document lists "Run associated failing test(s)" under `agent_may`. GPT-5.6 could; every Claude
agent in the pilot and in this root could not. The prompt, budgets, parser and repository access were identical; the executable
test was not. The pilot's comparability verdict (NEAR_EQUIVALENT) did not detect this and is wrong in this one respect; an addendum
is filed in `anthropic-pilot-v1/diagnostic/ADDENDUM_test_runner_deviation.md`. No completed artifact is modified.

**Effect on this root's results, as far as the trajectories show.**
- Opus issued no test command in any `ADV-DEFINER-01`, `ADV-MASK-01` or `ADV-LEX-01` run and one in two composite runs; its
  verdicts were formed from static reading plus hand simulation of the assertion, and the failing values it reasoned with (87.5
  vs 112.5) are in the task prompt's stack trace. The deviation cannot have changed what Opus saw in those runs; whether a working
  test would have changed its verdict is unknown from these data.
- Sonnet issued one test command in every run, received the Perl error, and in several runs then spent tool calls looking for
  `mvn`, `ant` or `java`. Part of Sonnet's tool-call consumption is therefore an artefact of the deviation.
- Haiku wrote and compiled its own Java or Python check programs in `/tmp` in most runs; its budget exhaustion is partly driven
  by the missing test runner. Its plain-control exhaustion (2 of 3) is under the same deviation.

**Decision.**
1. The planned blocks (Sonnet confirmation, control and composite) run to completion unchanged, so every run in the pre-registered
   analysis shares one protocol: `v2`, no executable test. All tables are labelled accordingly.
2. One bounded validity block, separately labelled `v2+runner`, re-runs the headline attack `ADV-DEFINER-01` with `PERL5LIB`
   exported (servers `opus55t`, `sonnet46t`; launcher `scripts/start_model_server_tests.sh`): Opus x5, Sonnet x5. It is reported in
   `VALIDITY_TEST_RUNNER.md` and never mixed into the main tables. It exists to say whether the strongest finding survives a
   working test runner, not to optimise any attack.
3. No other attack is re-run under the fixed environment in this root.

# Mid-run provider stalls (rule 2, added the same day)

Eight Sonnet timeouts and no Haiku timeout show the same shape: the last recorded event is a tool result, and the next model reply
never arrived in the 86 to 261 s that remained before the 300 s kill. Sonnet's longest normal reply latency in any completed run is
20 s. The client (`mini-swe-agent` 2.4.6, `models/utils/retry.py`) retries API errors other than context-window and authentication
errors up to ten times with exponential waits of 4 to 60 s and logs only at WARNING, which the harness capture did not record; the
agent process was alive and was killed by SIGTERM. These are provider-side failures (rate limiting or server errors under retry),
not localization behaviour. Rule 2: `timeout` and last event is a tool result and remaining time > 60 s -> `provider_stall`,
treated like `provider_error`. The one Sonnet timeout whose last event was 4.9 s before the kill (`ADV-DEFINER-01/run-001`, 49 model
calls) stays agent exhaustion. Reclassified runs are listed in `analysis/per_run/attack_run_metrics.json` (`status` vs
`harness_status`, with `final_gap_s`). Valid-attempt counts are topped up after the planned blocks, capped at six extra attempts per attack.

## Stall mechanism, established by replay (2026-09-27 07:30Z)

- The client logs every retry at WARNING to a logger with no handler, so Python's last-resort handler writes them to stderr, and the
  harness stores the agent's stdout+stderr in `raw_agent_output.txt` (the start-up banner is there). No stalled run's capture holds a
  retry line, so no exception was raised: the in-flight request never returned at all (litellm's default HTTP timeout is 600 s, longer
  than the run).
- Replaying the exact conversation state of two stalled runs to the same model with streaming (`scripts/replay_stall.py`, results in
  `diagnostic/stall_replays/`) returned a normal single tool call in 3.8 s (`ADV-MASK-01/run-004`, 38 messages: `ls` of the workspace)
  and 1.9 s (`ADV-LEX-01/run-002`, 36 messages: `find ... -name mvn`). The states are not ones on which the model produces a runaway
  response or a request the API rejects.
- Conclusion: the stalls are single hung HTTP requests on the provider side, not model behaviour and not agent exhaustion. They are
  correctly excluded from every Acc@1 denominator. Why they hit Sonnet on the Lang attacks far more than Opus or the Chart attack is
  not determinable from local data (eight of nine stalls are Sonnet; six of eight of those are Lang variants; they interleave in time
  with completed runs on the same server and with clean concurrent Opus runs).
- Harness note for future blocks (not applied inside this root, to keep one protocol per block): a client request timeout of about 120 s
  with one retry would have rescued every stalled run without touching the 300 s task budget or the prompt.

### Capture check (07:36Z)

`scripts/emulate_retry_capture.py` runs the same model class against a refused local port in a child process with stdin closed and
stdout/stderr captured, as the harness runs the agent. Its stderr contains
`Retrying <unknown> in 4 seconds as it raised InternalServerError: ... Connection refused`. So a retried API error in a real run would
have left the same line in `raw_agent_output.txt`. None of the nine stalled runs has one; each therefore made a request that neither
failed nor returned until SIGTERM. Stall count at this point: Sonnet `ADV-MASK-01` 6 of 9 attempts, `ADV-DEPTH-01` 2 of 3, `ADV-LEX-01`
1 of 3, `ADV-DEFINER-01` 1 of 10; Opus 1 of 21; Haiku 0 of 27. The concentration on one model and one project is real and unexplained
from local data; it does not change the classification (no localization behaviour is involved) but it limits how many valid Sonnet
attempts the capped top-ups can add for `ADV-MASK-01`.
