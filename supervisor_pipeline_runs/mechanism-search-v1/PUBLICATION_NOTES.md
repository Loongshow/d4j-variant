# Publication review notes

These notes apply to `mechanism-search-v1` and the companion `cue-trust-v3`
archive. The frozen drivers, plans, hashes and recorded results are historical
artifacts. They have not been rewritten to incorporate findings from this review.

## Reproduction scope

The scripts retain paths to the original experimental environment. The public
archive omits credentials, pristine project checkouts, workspaces and full model
transcripts; `cue-trust-v3` also omits its server copies and run directories.
Consequently, a fresh clone cannot run the archived drivers or independently
recompute all code-display measures without restoring those resources. Recorded
hashes can check the published artifacts; they do not establish that omitted
artifacts are present or unchanged in a new environment.

## Known issue in the frozen drivers

Both archives' `scripts/ct_driver.py` check source integrity with
`elif si and not integrity_ok`. A missing or malformed `source_integrity.json`
is read as an empty object, so this branch can be skipped and a behavioural run
can be accepted without positive integrity evidence. This is a defect in the
historical acceptance rule.

The included records checked during publication review do not exhibit this
condition:

- All 27 included cue-trust runs have `source_integrity_ok: true` in the driver
  ledger. Their original integrity reports are not part of the public snapshot.
- All 141 included mechanism-search runs have the same passing ledger flag and
  a published, passing `source_integrity.json` report.

These observations bound the issue in the recorded data; they do not make the
driver safe for new experiments. Before reusing it, require positive source
integrity evidence for every behavioural run, reject missing or malformed
reports, test the rejection paths, and freeze that corrected implementation as
a new protocol. The archived driver is retained unchanged so its recorded hash
continues to identify the implementation used for these experiments.

## Answer-key reconstruction fix

The unfrozen helper `scripts/mx_rebuild_key.py` previously treated derived
revisions like new builds. Their validation records use `status: READY`, whereas
new builds use `overall: READY`. As a result, rebuilding silently omitted two
valid Phase 4 variants and their six analysis runs. Their specs also inherit
metadata from a parent, which the old helper did not reconstruct.

The helper now handles both validation formats, resolves inherited metadata,
and writes the complete key by atomic replacement. Invalid parent references
and failed writes leave the existing key intact. Builders must finish before
reconstruction; atomic replacement does not lock their inputs. Regression tests
reconstruct all 43 archived entries in a temporary directory and compare every
field, adjusting only the relocated `fresh` path. The committed answer key and
results have not been regenerated or changed.

Run these tests from the repository root without credentials or project checkouts:

```sh
python3 -B -m unittest discover -s supervisor_pipeline_runs/mechanism-search-v1/tests -v
```

## Offline verification

Publication review checked script and data syntax, compared saved rankings with
the run summaries, and checked published freeze entries. The existing backend
tests and frontend build also passed. No provider calls or new Defects4J
experiments were made. Code-display measures could not be recomputed from the
omitted transcripts.
