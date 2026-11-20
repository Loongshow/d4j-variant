# Research code review guide

This fork contains research code for constructing Defects4J variants and
evaluating method-level fault localization. The upstream Defects4J framework
and its documentation are retained.

## Where to start

For the completed thesis main study, start with
[`results/main-study/`](results/main-study/README.md). It provides the 1,115
selected run rows, 223 instance rows, per-project results and a link to the full
investigation archive. The corresponding source, benchmark patches and audit
records are under
[`supervisor_pipeline_runs/weaker-model-v1/`](supervisor_pipeline_runs/weaker-model-v1/).

| Path | Purpose |
| --- | --- |
| `variant-lab/server/variantConstruction.mjs` | Variant construction and validation workflow |
| `variant-lab/server/reasoningWorkflow.mjs` | Research workflow orchestration |
| `variant-lab/server/variantLibrary.mjs` | Variant discovery, consistency and eligibility checks |
| `variant-lab/server/agents/miniSweAgentAdapter.mjs` | Agent execution adapter |
| `variant-lab/server/agents/mini_swe_fault_localization.py` | Repository investigation tools and ranked method submission |
| `variant-lab/server/benchmarkStore.mjs` and `accuracyStore.mjs` | Benchmark execution records and accuracy summaries |
| `variant-lab/server/__tests__/` | Regression tests |
| `variant-lab/src/` | Research application interface |
| `skills/d4j-variant-generator/` | Construction instructions and prompt references |

`supervisor_pipeline_runs/` contains experiment-specific source, including
builders, validation scripts, evaluation runners and analysis scripts. Begin
with a directory's `README.md` or protocol, then its `scripts/` directory.
The directories cover several exploratory stages; they should not all be
interpreted as conditions in one completed study.

## Run the application checks

The application uses Node.js and pnpm. From the repository root:

```sh
cd variant-lab
pnpm install --frozen-lockfile
pnpm test:server
pnpm build
```

To start the local application:

```sh
pnpm dev:full
```

For Defects4J itself, follow the Java, Perl and repository initialization
instructions in the upstream [README](README.md#setting-up-defects4j).
The application tests do not substitute for running a generated variant's
Java tests.

Checks completed for this publication snapshot:

- Server regression suite: 198 passed, 0 failed, 0 skipped.
- TypeScript checks and frontend production build: passed.
- Selected source syntax checks: 228 Python, 76 shell and 53 JavaScript files
  passed. These checks parse the experiment scripts without launching model
  experiments.

## Test data included in this branch

The regression suite includes the recorded depth-audit registry and the
complete small `CLOSURE-1-L10-STRICT-001` package under `new_bug_variants/`.
These files let the strict-artifact checks run in a fresh checkout. They are
test inputs, rather than the full generated benchmark corpus.

Two small publication checks were repaired in this review branch: the
depth-registry regression test now resolves its data relative to the test
file and checks the current four strict artifacts; one historical Python
analysis script uses equivalent formatting without a nested f-string.

## Experiment dependencies

End-to-end experiments require the relevant datasets, Defects4J checkouts,
tool installations and model credentials. Several historical scripts contain
machine-specific paths and expect archived run inputs. In particular,
`supervisor_pipeline_runs/run_real.sh` refers to an external chain generator
that is not contained in this repository. Review those paths and the stage's
protocol before using an experiment runner.

The Anthropic pilot retains its own server source snapshot because its
provider adapter differs from the main application. Other identical server
snapshots were not duplicated in this update.

Local credential files, installed dependencies and full project checkout
copies remain excluded. The thesis's large investigation archive is published
as a separate GitHub Release asset; see the main-study results page above.
Existing upstream documentation and licensing remain in place.
