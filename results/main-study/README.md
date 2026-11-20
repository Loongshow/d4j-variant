# Main study: 223 instances and 1,115 runs

These are the outputs of the thesis's main GPT-5.5 experiment, across 13
Defects4J projects. Start here for the 1,115-run results, rather than the earlier
pilot or Stage B experiments.

## Results you can read on GitHub

| File | Contents |
| --- | --- |
| [runs.csv](runs.csv) | The 1,115 valid runs used in the main study, one row per run |
| [instances.csv](instances.csv) | The 223 counted instances, one row per instance |
| [by_project.csv](by_project.csv) | Counts and rates grouped by project |
| [summary.json](summary.json) | Overall counts, selection rule and source-file hashes |
| [source_tables/](source_tables/) | The six original run and instance tables, unchanged |

Of the 1,115 valid runs, 1,114 submitted a ranking and one ended without an
answer. In 520 answered runs, the reference faulty method was not ranked first;
146 instances had at least one such run. The reference method was ranked first
in the other 594 answered runs.

The original columns are retained. `shift=True` means an answered run ranked
another method first; it is not a comparison with an untransformed baseline.
The instance-table column `instance_success` means the construction produced
at least one such misranking, rather than successful fault localization.

## Complete investigation records

Download the [thesis experiment archive](https://github.com/Loongshow/d4j-variant/releases/tag/thesis-main-study-2026-11-03).
The release includes the `.tar.gz` archive, a SHA-256 manifest, its summary and
the original archive README. Download the named archive asset; GitHub's
automatic **Source code** downloads contain the Git repository, not this data
archive.

After extracting it, individual main-study runs are under:

```text
thesis_materials/experiment/models/w55/benchmark_runs/
  mini-swe-agent-openai-gpt-5-5/<variant_id>/<run>/
```

Match `variant_id` and `run` from `runs.csv` to that directory. For example,
Lang-24 uses `CTV-03BC75/run-001` through `run-005`.

| Run file | Contents |
| --- | --- |
| `mini-swe-agent.traj.json` | The recorded investigation: messages, commands and returned outputs |
| `ranking.json` | The submitted method ranking |
| `fault-localization-submission.json` | The structured submission |
| `evaluation.json` | The ranking's evaluation against the reference answer |
| `prompt.txt` | The rendered task given to the agent |
| `run_manifest.json` | Run identity, settings and status |

The archive has 1,136 historical main-study run folders. The headline 1,115
excludes 11 attempt records and ten runs from two flagged instances,
`MI-Cli-11` and `MI-Math-96`. To reproduce the selection, join each original
`*_RUNS.csv` to its paired `*_RESULTS.csv` on `instance_id`, then require
`included=True` and `counted_in_kpi=True`.

The archive also contains 121 Stage B run folders. These are separate
experiments and are not included in `runs.csv`.

## Construction, prompts and analysis

The browsable [main-study source and benchmark artifacts](../../supervisor_pipeline_runs/weaker-model-v1/)
include:

- `scripts/`: construction, validation, execution and analysis scripts;
- `construction/mainrun/`: construction briefs, specifications, designs and audits;
- `instances/<instance_id>/`: validation and correct, faulty and test patches;
- `new_bug_variants/`: the 223 counted packaged variants;
- `review/VARIANT_KEY.json`: reference answers, also including earlier study instances;
- `main-run/`: original result tables, analysis, annotation and integrity records;
- `plans/`: recorded execution plans;
- `models/w55/variant-lab/server/`: the frozen evaluation server, including prompt templates;
- `PUBLICATION_MANIFEST.sha256`: hashes of the 3,021 unchanged snapshot files committed here.

The full archive additionally contains the thesis analysis scripts under
`thesis_materials/thesis/analysis/` and two helper modules under
`thesis_materials/helpers/`.

## Reproduction scope

This publication preserves the November 3 snapshot. The archive's original
README explains how to recompute the reported counts after adjusting its
machine-specific paths. Some older record checks need inputs omitted from the
archive; the snapshot is not a one-command installation or a new experiment.
Its thesis sources are an earlier draft, not the final submitted document.

Credentials, environment files and the credential-bearing server launcher are
withheld. Full project checkouts and most workspace copies are also omitted;
they can be reconstructed from Defects4J and the recorded patches. The saved
trajectories and gold source copies remain available in the archive.

The frozen driver retains a known integrity-check limitation: missing or
malformed integrity evidence can escape one rejection branch. Read the
[publication inventory](PUBLICATION_INVENTORY.md) before reusing it. Any new
experiment needs a corrected, tested implementation and a new protocol freeze;
the historical scripts and results have not been rewritten.
