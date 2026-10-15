# Replay selection (fixed before any replay call, 2026-10-15)

Rule: among the timeouts that had read the gold in full (9 of 10), the two with the longest pending final model call (final
gap) on different instances, plus the timeout with the most calls after the gold first appeared. One request each, capped at
240 s, from the exact pre-timeout state; diagnostic only, never scored.

- CTV-7CE456/run-002 (HO-HC-JACKSONCORE-01): final pending call 59.4 s; calls after gold 8
- CTV-E04F64/run-005 (HO-HA-JACKSONCORE-01): final pending call 39.2 s; calls after gold 6
- CTV-E65CBB/run-002 (HO-HB-MATH-01): final pending call 7.9 s; calls after gold 33

Ranking used: CTV-7CE456/run-002 59.4 s, CTV-E04F64/run-005 39.2 s, CTV-E04F64/run-004 37.8 s, CTV-21982A/run-002 36.8 s, CTV-7CE456/run-003 17.3 s, CTV-E65CBB/run-004 14.1 s, CTV-E65CBB/run-002 7.9 s, CTV-9CE7EA/run-003 6.9 s, CTV-21982A/run-004 3.6 s
