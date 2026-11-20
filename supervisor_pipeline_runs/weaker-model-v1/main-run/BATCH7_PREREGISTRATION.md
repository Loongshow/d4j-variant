# Main run, batch 7 (cell C10i, the paired static/instance bridge): pre-registration

Written on 26 October 2026, before any batch-7 design, build or run, while the batch-6 runs are in progress. The sha256 of this file is
recorded in `AMENDMENTS.md` (W50). Batch 7 is the third tier of the "all Defects4J bugs" extension (W42, W45): the paired bridge of the
13-day plan. It answers one question the extension raised: **does the facade's kind (static vs instance method) change the result on the
same bug, with the same hosts?** Without this, the C10i instances that the full extension would need could not be compared with the 105
static-facade instances.

## Authorisation

W45 (the user's standing instruction of 25 October) and the approved plan (`PLAN_ALL_BUGS_ZH.md`, "配对桥接约 20 个"). The $500 sanity cap
and the per-block checks of W45 remain.

## Design

**Unit.** A bug that already has an ACCEPTED static-facade instance (C10 or C10f) and offers a strictly-tested instance-method candidate
(profile of 23 October: variant V0–V2, feasible, called by a test under the strict check, public top-level class, not the static facade).
Of the 105 ACCEPTED bugs, 30 qualify; 19 are selected (the 11 others have 4–8-line wrapper candidates, or a private nested class; listed in
`main-run/batch7_prep/selection.md`). The 19 come from batches 1, 3, 4, 5 and 6 (C10 and C10f).

**The paired instance.** The same fixed revision, the same fixture, the same five host classes in the same hop order as the static instance
(`hosts_hop_order` in the task record; drawn once, by the static instance's seeded draw or the largest5 rule), a different facade: an
instance method rewritten as state gathering plus one call to hop 1 (`BUILD_BRIEF_C10I_ADDENDUM.md`, sha256
`3be3eafbfcd8…`): variants V1 (state as parameters), V2 (receiver as parameter), V3 (same-package hosts,
only where listed), V4 (private helpers pre-computed in the facade), V5 (generic hops). Not allowed: widening visibility, new types,
reflection, signature changes, test edits. Hops, gold (quiet one-line omission), facade lie, existing trigger, 16 gates, audit, blind trace
check, one redesign and the disposition table are unchanged from batches 3–6. The builder may not read the static instance's design, spec,
patches or audit (addendum §2). Reachability probe mandatory (addendum §4).

**Labels and paths.** `scripts/mr3_spec.py` (sha256 `f4e673bd7697…`): a copy of `mr_spec.py` with instance id `MI-<key>`, group
`MI-<key>`, mechanism and tier `MAIN_RUN_C10I`, scratch `/private/tmp/d4j-mi-*`. Designs are `designs/<key>__i.py`; specs `specs/MI-<key>.json`;
instances `instances/MI-<key>/`; audits `audits/MI-<key>.json`; task keys `<key>__i` with `fixture_key = <key>`. Records are written by
`scripts/mr3_build_records.py` (`b09afad8f564…`) to `INSTANCE_BUILD_LOG_C10I.csv` and `INSTANCE_PROVENANCE_C10I.csv`
(the C10/C10f files are not touched), and the cell is reported by `scripts/mr3_report.py` (`5266ddd6c3bf…`): `MAIN_RUN_C10I_*`.
`mr_validate.py`, `mr_package.py`, `mr_key.py`, `mr_gold_text.py`, the frozen driver, scanner, metrics and server are unchanged.

**KPI and reading (all descriptive; no thresholds beyond those stated).**
- Per instance, as always: SHIFT = gold rank > 1; INSTANCE_SUCCESS = at least one shift in 5 valid runs.
- **Primary (paired):** over the pairs whose instance facade is distinct (15 of 19 if all build), the within-bug difference
  "instance-facade shifted runs / answered" minus "static-facade shifted runs / answered", reported per pair and as a mean with its sign
  test; and the count of pairs where the instance side succeeds vs where the static side succeeds (a 2×2 over pairs).
- **Secondary:** the C10i cell on its own (instances tested, with a shift, shifted/answered, per project); all pairs including recorded
  reuse; by facade variant (V1 vs V2) and by host regime.
- Rank-1 category: for an instance facade, ENTRY_POINT_BIAS keeps its meaning (the facade is the entry point); a new rank-1 category that
  appears (for example a public method of the receiver) is reported as its own count.

## Candidates (19)

Source `main-run/bridge7_tasks.json` (sha256 `abedf91782c0…`). Allowed targets are the up-to-three best instance candidates
(variant order V0 < V1 < V2, then self-containedness); the builder picks one; the paired static facade is excluded.

| Rank | Task | Paired static instance (batch) | Static facade | Allowed instance facades | Best variant | Hosts | Instance-facade reuse of |
|---|---|---|---|---|---|---|---|
| 191 | Codec-11__i | MR-Codec-11 (batch6) | QuotedPrintableCodec.decodeQuotedPrintable | QuotedPrintableCodec.encode / QuotedPrintableCodec.decode | V2 | largest5 | — |
| 192 | Codec-8__i | MR-Codec-8 (batch6) | Base64.encodeBase64 | Base64InputStream.read / Base64.decode / Base64.encode | V2 | largest5 | — |
| 193 | Collections-13__i | MR-Collections-13 (batch6) | ExtendedProperties.convertProperties | ExtendedProperties.getInclude / ExtendedProperties.setInclude | V1 | largest5 | — |
| 194 | Collections-5__i | MR-Collections-5 (batch6) | SetUniqueList.decorate | SetUniqueList.addAll / SetUniqueList.add | V2 | largest5 | — |
| 195 | Collections-15__i | MR-Collections-15 (batch6) | SetUniqueList.decorate | SetUniqueList.addAll / SetUniqueList.add | V2 | largest5 | Collections-5__i |
| 196 | Collections-16__i | MR-Collections-16 (batch6) | SetUniqueList.decorate | SetUniqueList.addAll / SetUniqueList.add | V2 | largest5 | Collections-5__i, Collections-15__i |
| 197 | Collections-19__i | MR-Collections-19 (batch6) | SetUniqueList.setUniqueList | SetUniqueList.retainAll / SetUniqueList.add | V2 | largest5 | — |
| 198 | Collections-21__i | MR-Collections-21 (batch6) | SetUniqueList.setUniqueList | SetUniqueList.retainAll / SetUniqueList.add | V2 | largest5 | — |
| 199 | JacksonCore-1__i | MR-JacksonCore-1 (batch6) | NumberInput.inLongRange | TextBuffer.contentsAsString / TextBuffer.size / TextBuffer.expandCurrentSegment | V1 | largest5 | — |
| 200 | JacksonDatabind-103__i | MR-JacksonDatabind-103 (batch6) | ClassUtil.isLocalType | BasicBeanDescription.findAnySetterAccessor / DeserializationContext.isEnabled / SettableBeanProperty.deserialize | V1 | 1500 | — |
| 201 | Lang-22__i | MR-Lang-22 (batch1) | Fraction.getFraction | Fraction.toProperString / Fraction.pow / Fraction.hashCode | V2 | 1500 | — |
| 202 | Lang-49__i | MR-Lang-49 (batch3) | Fraction.getReducedFraction | Fraction.toProperString / Fraction.pow / Fraction.hashCode | V2 | 1500 | — |
| 203 | Lang-38__i | MR-Lang-38 (batch4) | FastDateFormat.getInstance | FastDateFormat.format | V2 | 1500 | — |
| 204 | Math-36__i | MR-Math-36 (batch4) | BigFraction.getReducedFraction | BigFraction.doubleValue / BigFraction.floatValue / BigFraction.pow | V1 | 1500 | — |
| 205 | Math-55__i | MR-Math-55 (batch3) | Vector3D.angle | Vector3D.orthogonal / Vector3D.normalize | V2 | 1500 | — |
| 206 | Time-12__i | MR-Time-12 (batch5) | LocalDateTime.fromDateFields | LocalDate.toDate / LocalDateTime.toDate / LocalDate.toDateTime | V2 | 1500 | — |
| 207 | Time-9__i | MR-Time-9 (batch5) | DateTimeZone.forOffsetMillis | DateTimeZone.getOffsetFromLocal / DateTimeZone.getMillisKeepLocal / DateTimeZone.getOffset | V2 | 1500 | — |
| 208 | Time-17__i | MR-Time-17 (batch5) | DateTimeZone.setProvider | DateTimeZone.getOffsetFromLocal / DateTimeZone.getMillisKeepLocal / DateTimeZone.getOffset | V2 | 1500 | Time-9__i |
| 209 | Time-19__i | MR-Time-19 (batch5) | DateTimeZone.forOffsetHoursMinutes | DateTimeZone.getOffsetFromLocal / DateTimeZone.getMillisKeepLocal / DateTimeZone.getOffset | V2 | 1500 | Time-9__i, Time-17__i |

Expected: several UNBUILDABLE outcomes (short methods; write-back or receiver semantics that no single owner can carry), recorded with
their reasons. Reuse within the cell (three `SetUniqueList.addAll`, three `DateTimeZone.getOffsetFromLocal` bugs) is recorded, not forced
apart: the pair comparison is within bug, and the three bugs differ in revision and in their static instance.

**Key preflight.** No `designs/<key>__i.py`, `specs/MI-<key>.json`, `instances/MI-<key>/`, `audits/MI-<key>.json` or `history/<key>__i/`
exists for any of the 19; every fixture exists. Checked on 26 October: clean.

## Cost guard and runs

Plans `plans/MR_batch7_block<N>_gpt55.json` in batch-7 order, blocks of at most 5, 5 runs each; `mr_run_blocks.sh` with cap $500. Expected
run cost at most 19 × 5 × $0.43 ≈ $41 if every candidate builds; cumulative after batch 6 is projected at about $290.

## Integrity

- Batch-6 manifest (`b6_integrity_manifest.json`) recorded after the batch-6 runs and before any batch-7 row.
- `mr_integrity.py --verify-frozen batch7_frozen_hashes.json`, written before any batch-7 build: every `mr_*`, `mr2_*` and `mr3_*` script,
  the briefs, the checklist and both addenda, this document, `bridge7_tasks.json`, the batch-1–6 task files and dispositions, the pool
  files, the manifests, the other servers' ledgers, and `AMENDMENTS.md` through W49 as a pinned prefix.

## Outputs

`main-run/bridge7_tasks.json`, `bridge7_build_audit_results.json`; `analysis/bridge7_dispositions.json` (with `facade_variant`,
`state_passed`, `facade_reuse_of`, `paired_instance`), `bridge7_trace_checks.json`, `bridge7_trace_robustness.json`,
`batch7_frozen_hashes.json`; `INSTANCE_BUILD_LOG_C10I.csv`, `INSTANCE_PROVENANCE_C10I.csv`; the `mr3_report.py` files; a paired-analysis
table `analysis/bridge7_pairs.json`; `SUPERVISOR_PROGRESS_UPDATE.md` as update 6 (with batch 6).
