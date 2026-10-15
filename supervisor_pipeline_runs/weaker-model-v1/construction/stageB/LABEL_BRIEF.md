# Stage B blind labelling brief (misses only; two lenses per run, then adjudication)

You label ONE run of an LLM fault-localisation agent that ranked the wrong method first. You are told the run id, the project,
and where to find the safe trajectory view and the two patches. You are NOT told the experimental cell, and you must not infer
or mention it in your label beyond what the code shows. Work only from these inputs:

    WM=/Users/shawnli/Desktop/Honours/defects4j/.claude/worktrees/strict-depth-experiment-run-524113/supervisor_pipeline_runs/weaker-model-v1
    safe view:   $WM/analysis/traj_views/<variant>/<run>.txt   (produced by scripts/mx_traj_view.py; contains tool calls, displayed
                 file excerpts, test output and the final submission; hidden reasoning fields are removed)
    patches:     $WM/new_bug_variants/<Project>/bug-1/L20/<variant>/variant.patch and test.patch
    key entry:   the gold, decoys, entry point and evidence methods for the variant (given to you in the task)

Never open anything else under models/, benchmark_runs/, workspace_archive/, raw_agent_output.txt, probe_*.json,
diag_run_response.json or .env files.

## Lenses

- **Process lens**: what the agent read, ran and saw, in order; where the gold's faulty line was first displayed; whether the
  agent read the gold in full; which tests it ran; which evidence methods (second callers, sibling implementations) it displayed.
- **Argument lens**: the premises of the agent's final evidence chain, each checked against the patches and the displayed code;
  whether the method ranked first actually violates its documentation on the trigger input; whether the agent's own narrative
  located the divergence at the gold before ranking another method.

## Labels (the preregistered Phase 7 set; one primary, optional secondary)

SEARCH_FAILURE (gold never displayed) | DISCOVERY_WITHOUT_INSPECTION (displayed, not read in full) | EVIDENCE_RETRIEVAL_FAILURE
(decisive evidence available but never fetched) | EVIDENCE_INTEGRATION_FAILURE (decisive evidence displayed but not used) |
CONVENTION_PRIOR (blamed the hop that defines or applies a convention instead of the hop that violates it) | LOCAL_ODDNESS_BIAS
(blamed code because it looks unusual although it is correct) | ENTRY_POINT_BIAS (ranked the method the test calls, or a facade,
first) | LEXICAL_SHORTCUT (ranked by name or vocabulary match) | ATTRIBUTION_FAILURE (read the gold, misattributed, none of the
above fits) | OTHER (explain).

Also record: `defensible` (yes / partly / no): would a careful engineer accept the rank-1 method as the fault location given the
project's documentation and tests? `gold_named_in_chain` (did the agent name the gold anywhere in its final evidence chain?),
`divergence_located_at_gold` (did the agent's own narrative place the first wrong value at the gold?).

Output: JSON `{"run": ..., "lens": "process"|"argument", "primary": ..., "secondary": ... | null, "defensible": ..., "gold_named_in_chain": ...,
"divergence_located_at_gold": ..., "evidence_displayed": [...], "rationale": "<= 120 words"}`. Final message: the JSON only.
