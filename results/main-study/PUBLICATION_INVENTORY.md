# Publication inventory

This inventory distinguishes the completed main study from earlier experiments
and from resources deliberately excluded from publication.

## Main-study materials added

The original `main` branch did not contain `weaker-model-v1`, where the completed
thesis study was carried out. This update adds the following unchanged snapshot
files under `supervisor_pipeline_runs/weaker-model-v1/`:

| Material | Coverage |
| --- | --- |
| Experiment scripts | 87 source and provenance files, excluding the credential-bearing launcher |
| Frozen plans | 89 plan files |
| Frozen server and configuration | 38 source/configuration files |
| Construction | Specifications, designs and independent audits for all 223 counted instances, plus the briefs |
| Validation and patches | Validation evidence and correct, faulty and test patches for all 223 instances |
| Packaged benchmark | All 223 counted variants |
| Reference answers | The recorded answer key, which also contains earlier instances |
| Result evidence | Original tables, analysis, annotation and integrity records |

The 3,021 copied files total 46,715,376 bytes and match their hashes in the
November 3 snapshot. `PUBLICATION_MANIFEST.sha256` records their repository
paths and hashes. The convenient `results/main-study/*.csv` files are new
selections of these original tables; their source hashes and selection rule
are in `summary.json`.

The separate release archive contains 29,410 files, including the complete saved
investigations for 1,136 historical main-study runs and 121 Stage B runs. The
main study counts 1,115 valid runs from 223 instances; the other records remain
available for auditing exclusions.

## Known integrity-check limitation

The frozen `scripts/ct_driver.py` retains the condition
`elif si and not integrity_ok`. Missing or malformed integrity evidence can
therefore escape this rejection branch. Publication does not retrospectively
change the implementation that produced the records.

A read-only check of the 1,115 counted runs found all 1,115 latest ledger flags
`source_integrity_ok` explicitly true, and all 1,115 original
`source_integrity.json` files present, parseable and explicitly `ok: true`.
These observations concern the recorded runs. Before using the driver for new
experiments, correct and test the missing-evidence path and establish a new
protocol freeze.

## Additional local materials not included in this update

These omissions do not remove any of the counted main-study run records:

| Material | Status |
| --- | --- |
| Stand-alone historical chain generator | Eight Python files, about 93 KB, under the author's separate `Honours/thesis/` directory. Not separately published here; the main-study snapshot has its own generator sources under `scripts/generator/`. The stand-alone version also refers to an unavailable external call-graph module. |
| Older exploratory reports | 111 direct-child Markdown reports across earlier experiment folders, including research audits; not added wholesale to the main-study publication. |
| Early consolidated results | The 11-file `thesis-results-current/` folder, about 43 KB, summarizes an earlier study stage and is not the 1,115-run result set. |
| GPT-5 timeout diagnostics | The separate `weaker-model-v1/gpt5-timeouts/` folder, 51 files and about 1.15 MB, is absent from the November 3 snapshot. |
| Later figure edits | Eight figure or plotting-script files differ from the snapshot, including the tier-trend and Stage B comparison plots. This publication preserves the audited snapshot versions. |
| Final thesis and presentation | Not separately published as final documents. Thesis sources inside the archive are an earlier draft. |

The current application source and the previously published exploratory script
selection were also checked. No additional missing application implementation
was found in that scoped comparison; most local dirty files already match
`main`. Existing publication fixes are retained.

## Deliberately excluded resources

Credentials, `.env` files and the credential-bearing server launcher remain
private. Dependencies, caches, pristine Defects4J checkouts, symbolic links and
duplicate runtime copies are not uploaded. Most workspace source copies can be
rebuilt from the fixed revision and patches; the snapshot retains the gold
source files needed by its exposure analysis.

Raw provider-output text, diagnostic probes and some earlier or held-out run
folders are not in the archive. The original archive README identifies these
limits and the reproduction entry points. In particular, some historical
record-check scripts depend on omitted inputs; do not interpret a missing
input as a verified negative result.
