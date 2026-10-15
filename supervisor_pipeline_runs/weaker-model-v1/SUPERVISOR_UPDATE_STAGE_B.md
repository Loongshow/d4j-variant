Hi Hong Jin,

Stage B is done: the chain-isolated drop exists on a current model, and it is large.

**Design.** Three fresh bugs, one per project, each a 2x2 with 5 runs per cell on gpt-5.5 under the frozen protocol
(same prompt, tools, 50-call / 300 s budget and scoring as everything before). Within a bug all four cells share the fault line,
the trigger test and the failing value; the gold is never the method the test calls. Factor 1, your recipe as code: the fault's
step moved five hops below the facade, each hop inserted at a seeded anonymous point in a different existing class of 1500+ lines
(host_search / insertion-anchor functions vendored from your generator), with a procedural lie in the facade javadoc. Factor 2, the
CHART-PIE-03 ingredient: one correct hop (or, in the 1-hop cells, a sibling helper) written in a valid but locally odd form. Golds
are omissions inside an iteration whose effect no caller can pre-filter or recover with a one-line repair that keeps the hop in use
(bypasses through other implementations exist for all three and are recorded; see point 1 below): Lang `StringUtils.indexOfAnyBut`
(the membership test omits the second unit of a surrogate pair), Chart `DatasetUtilities.findStackedRangeBounds` (NaN admitted
into the negative total), Math `StatUtils.mode` (the NaN skip omitted from the frequency tally). Every cell passed the 16
construction gates and an independent ownership audit before any run.

**Result (60 runs, all answered, none contaminated, $21.91).**

| Cell | Acc@1 (n = 15) | Lang | Chart | Math |
|---|---|---|---|---|
| 1-hop, plain | 15/15 | 5/5 | 5/5 | 5/5 |
| 1-hop, odd sibling | 14/15 | 4/5 | 5/5 | 5/5 |
| 5-hop chain + lie, plain hop | 3/15 | 1/5 | 2/5 | 0/5 |
| 5-hop chain + lie, odd hop | 4/15 | 0/5 | 4/5 | 0/5 |

Chain main effect: 7/30 against 29/30, a drop of 0.73, Fisher p = 3.4e-9, same direction in all three projects. Odd-hop main
effect: 18/30 against 18/30, nothing. The preregistered expectation was that the chain cell would stay near ceiling unless the
lie plus the 5-hop chain did work the earlier 2-hop test had not revealed, with the odd-hop cell lowest and the interaction the
quantity of interest; the data put all of the measured drop in the chain arm, and the odd hop adds nothing on average (Chart's
odd-hop chain cell was 4/5 against 2/5, Lang's 0/5 against 1/5, n = 5).

**What the agent does.** Two blind labellers per miss (process and argument lens), disagreements adjudicated, 24 misses. In 24 of
24 the gold is named in the final evidence chain; in 22 the agent's own narrative places the first wrong value at the gold's fault
line; it then ranks the facade first (17 ENTRY_POINT_BIAS, 6 CONVENTION_PRIOR where the facade's javadoc is the only statement of
the convention, 1 odd-hop-first by role). No search failures by the labels: the chain cells cost 19 tool calls against 11-13 but every run finished inside the
budget, the fault line was displayed in all 24 misses and the frozen measures record the gold read in full in 21 (the other 3 are a
display-matcher gap, W16). Two Lang runs ran jshell differentials that isolated the char-array path as wrong and the CharSequence
overload as right, and still ranked the two-line delegating facade first; the stated reasons across runs are "the direct failing
API", "the overload under test", "the primary repair location". No evidence chain cites the facade lie. So the drop is a ranking
decision after a correct diagnosis, not a reading or budget failure.

**Two things you should know about the construction.**
1. Ownership rule. The first Chart audit rejected the bug because the facade can be rewritten in one line to recompute the bound
   from an unrelated existing method, leaving the gold's output dead. I refined the preregistered single-owner rule before any
   run: a one-line edit at another method counts as a competing repair only if it keeps every hop's documented output in use; an
   edit that replaces the gold's result with another implementation is a bypass, recorded but not a second owner (AMENDMENTS W13).
   Under that rule Lang, Chart and later Math were confirmed, each with a recorded bypass. Math's first design (an atanh series
   tier) was rejected under the audit's if-uncertain-reject rule: a half-angle argument reduction at the facade keeps the gold in
   use and passes every test, which the auditor classed as a competing repair while noting it sits close to a bypass; it was
   replaced by the StatUtils.mode design (W14, W15).
2. Fixture incident. Adapting your harness-staging check to this root, I passed it a symlinked fixture path; the server's copy
   routine makes the destination a symlink and its history-stripping step then deleted `.git` (and Chart's `.svn`) in three
   shared mechanism-search fixtures (Lang, Math, Chart). No tracked file changed (verified byte for byte against fresh checkouts);
   Shawn has the one-line restore from the server's identical checkouts and the decision. This root now uses its own checkouts and
   the check refuses symlinks (W12).

**Limits.** Three bugs, 15 runs per cell; gpt-5.5 only, GPT-5.6 not re-run. The chain arm bundles hop count, cross-class
dispersal, host size, anonymous placement and the lie; which of them carries the effect is not separated. A bypass exists for each of
the three bugs (recorded in the audits). One frozen measure (`gold_exposed`) misses `nl | grep` output in 3 of 24 misses; the
frozen value is kept and both readings are reported (W16).

**Proposed next block (your call, about $26: all cells are 5-hop and cost about $0.43 a run).** Same three bugs, 5 runs per cell, separating the bundle: 5 hops inside the
facade's own class vs 5 hops across five hosts, with and without the lie. That tells us whether it is the reasoning distance,
the dispersal into large foreign files, or the narrative that moves the rank.

Spend: $21.91 for Stage B; about $51 in this root including smokes (health probes about $1 more); about $80 across both roots.
The ladder preregistration's $40 check-in point was passed during block 1; I did not pause there because this block had been
approved at about $20 with a $25 cap, which held, but you should know it was crossed without a check-in.

Best regards
