## Reading

**Opus (v2+runner, n=5).** Gold ranks 2, 2, 2, 2, 1; Acc@1 0.2; MRR 0.60, against 2, 3, 2, 2, 3 (Acc@1 0.0, MRR 0.43) under v2. One run
(run-001) executed `defects4j test` and received the real ant output (`Failing tests: 1 ... expected:<87.5> but was:<112.5>`); it still
ranked `drift` first with the same argument as every v2 miss. The other four runs issued no test command at all, exactly as under v2.
The single hit (run-005) came, as in the composite's single hit, from a caller grep over `source/ tests/` that surfaced
`PlotUtilitiesTests`, which Opus then read: "drift = p1-p2 is fixed by PlotUtilitiesTests.testDrift ... the sign error is in nudge".
Under either protocol the deciding event is reading the pinning test, not running the failing test. The headline result
therefore survives the test-runner fix on both models: definer attribution with a non-terminal gold gives Acc@1 0.0 to 0.2 across fifteen Opus runs
(five v2, five composite, five v2+runner), with both hits produced by one broader search command.

**Sonnet (v2+runner, n=5).** Gold ranks 5, 5, 5, 5 in the four answered runs and one budget exhaustion: Acc@1 0.0 over five valid attempts, the same as under v2 (ten valid attempts, seven answers all at rank 5). The failing test executed through ant in 5 of 5 runs and returned the real `expected:<87.5> but was:<112.5>` output; 1 of 5 runs opened the pinning unit test. Every answer ranked `drift` first with the same reasoning as under v2. For Sonnet the working test runner changed neither the verdict nor the ordering; the deviation is not what made Sonnet wrong on this attack.

**What the block does not claim.** It is five runs per model on one attack; it shows whether the strongest finding depends on the
missing runner, not what the whole root would look like under the fixed environment. The main tables stay under protocol v2.
