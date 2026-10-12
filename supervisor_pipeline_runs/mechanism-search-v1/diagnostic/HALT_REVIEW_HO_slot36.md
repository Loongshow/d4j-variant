# Halt review: HO_cont slot 36 (HO-HB-COMPRESS-01, round 5)

- **Halt:** `HALT: slot 36 (CTV-1DA29F) failed twice as infrastructure`, at 2026-10-11T13:50:23Z.
- **Both attempts were provider stalls.** Both are classified `provider_stall` under rule 2 of the frozen uniform rule: a
  harness timeout, a tool result as the last recorded event, and more than 60 s left before the kill.

| Attempt | API calls | Final gap before kill | Cost (USD) |
|---|---|---|---|
| run-005 | 5 | 272.1 s | 0.109 |
| run-006 | 4 | 281.0 s | 0.092 |

- **Same instance, other rounds:** rounds 1 to 4 (run-001 to run-004) were valid, with the gold at rank 1 each time.
- **Replay diagnostic** (`scripts/replay_stall_gpt.py`, as in the pilot's slot-8 review). The exact conversation state of
  run-006 (18 messages, last role `tool`) was replayed to the same model with the same tools and model_kwargs, with a cap of
  240 s. It returned in **8.3 s** with `finish_reason=tool_calls` (3 tool calls, 12,312 prompt tokens). Record:
  `diagnostic/stall_replays/replay_CTV-1DA29F_run-006_halt36.json`.
- **Conclusion:** the stall is transient and provider-side, not caused by the instance's request. A third stall on this
  block, HO_cont slot 1 (HO-HA-COMPRESS-01, run-002), was replaced automatically by the driver and is valid.
- **Action under the preregistered top-up rule** (one top-up after a halt review, at most 2 per cell): `plans/HO_top.json`
  holds one slot, HO-HB-COMPRESS-01 round 5. It is frozen before the call. Both stalled attempts stay recorded as
  infrastructure and are never scored.
