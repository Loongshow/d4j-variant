# locally-coherent-conversion-v1 — NON-CANONICAL · CONSTRUCTION / VALIDATION ONLY · NO PAID MODEL EXECUTED

Matched pair CONVERSION-CONTROL-01 / CONVERSION-TREATMENT-01 on Lang-1f around `Conversion#intArrayToLong`, built deterministically
(no LLM) with a LOCALLY COHERENT fault: the destination bit offset is treated as a word index (`shift = (i + dstPos) * 32`).
CONTROL keeps the fault in place; TREATMENT keeps the facade's guards and relocates the loop behind `ArrayUtils.foldValues` -> `Fraction.assemble`.
Trigger `ConversionTest::testLang1112` (dstPos = 8 and 16; the existing suite only uses dstPos = 0).

Layout: CONVERSION-CONTROL-01/, CONVERSION-TREATMENT-01/ (packages) · analysis/ (contract, candidates, coherence audit, selection,
equivalence, leakage/information distance, NumberUtils comparison, readiness, prepared experiment, scripts, data) · validation/ · repro/ ·
work/ (construction checkouts) · EXPERIMENT_MANIFEST.json · LOCALLY_COHERENT_CONVERSION_REPORT.md.
This is NOT a reasoning-depth experiment; manifests carry `synthetic_call_hops` and mark `reasoning.level` as a legacy discovery slot.
