# Provider-stall rule (added 2026-09-27 during the composite block)

**Observation.** `opus55 / ADV-COMPOSITE-01 / run-002` ended with harness status `timeout` after 299,993 ms, but the
trajectory holds exactly one model call (cost 0.015 USD) and one executed command, issued at the start of the run.
The agent then waited on the provider until SIGTERM; `raw_agent_output.txt` contains only the config banner. Three
fast probes passed immediately afterwards and runs 003 and 004 completed normally.

**Rule (applied uniformly to every run in the root, past and future).** A run whose harness status is `timeout` and
whose trajectory holds at most two model calls and at most two executed commands is reclassified as
`provider_stall`. It is treated like `provider_error`: excluded from every Acc@1 denominator, counted in the
"provider errors" column, never counted as a localization miss. The original harness status is kept in the
`harness_status` field of `analysis/per_run/attack_run_metrics.json`; no run artifact is modified.

**Rationale.** The brief forbids counting provider errors as localization misses. A timeout in which the agent
worked steadily to the deadline (17 to 49 model calls in every other timeout in this root) is agent exhaustion
and stays a miss. A timeout in which the agent never received a second response is a provider failure that the
harness happened to surface as `timeout` because the client's retry loop outlasts the 300 s kill.

**Effect on the data.** Exactly one run is reclassified (listed above). To keep the composite's planned Opus
sample at five completed-or-exhausted attempts, one replacement run is queued after the block (`--planned 6`);
the stalled run stays in place and in the per-run table.

## Rule 2 (mid-run stall), added after the Sonnet MASK block

See `PROTOCOL_DEVIATION_TEST_RUNNER.md`, second section. Eight Sonnet runs reclassified; evidence is the final gap between the last
tool result and the kill (86 to 261 s) with the agent process alive and no further model reply.

## Mechanism

Established by replaying two stalled states with streaming: both answered normally in under four seconds, and no retry warning was
captured, so each stall was one HTTP request that never returned. Details: `PROTOCOL_DEVIATION_TEST_RUNNER.md`, last section.

## Rule 3 (context overflow is agent exhaustion, not infrastructure)

One run (`haiku45 / ADV-LEX-01 / run-002`) carries harness status `provider_error` because the API refused the 44th request with
`prompt is too long: 643678 tokens > 200000 maximum` (litellm `ContextWindowExceededError`, an abort exception, so no retry). The
request was oversized because of what the agent had read; the provider behaved correctly. The run is reclassified `context_overflow`,
counted as a no-answer (a miss over all attempts) with taxonomy class CONTEXT_LOSS, and is not excluded. Applied uniformly: it is the
only run in the root with that signature.

## Final count

Twenty hung requests in 131 runs: nineteen on claude-sonnet-4-6 (fourteen on Lang variants, five on Chart) and one on claude-opus-5-5; none on
claude-haiku-4-5 or on the two v2+runner servers. All excluded; stalled attempts topped up to ten valid attempts per confirmed attack
(`ADV-MASK-01` needed six extra launches, `ADV-LEX-01` four, `ADV-DEFINER-01` one, the control three).
