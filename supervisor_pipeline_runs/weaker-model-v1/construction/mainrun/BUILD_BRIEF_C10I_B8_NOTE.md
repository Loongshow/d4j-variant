# Batch 8 note to the C10i addendum (instance-method facades on bugs that have no static facade)

`BUILD_BRIEF.md` and `BUILD_BRIEF_C10I_ADDENDUM.md` apply in full, with these three differences for batch 8 (`main-run/BATCH8_PREREGISTRATION.md`):

1. **No static pair.** The bug has no static-facade instance (pool v2 found no strictly tested public static method of 4–50 lines in its
   modified classes). Addendum §2 (independence from the static instance) therefore has nothing to refer to; the task record's
   `paired_*` fields are null. Everything else in the addendum holds: the facade is one of the task's allowed instance methods, rewritten as
   guard + state gathering + one call to hop 1 (variants V1–V5, smallest that carries the computation; the not-allowed list), the gold is
   a quiet one-line omission in hop 5, the facade lie goes in the facade's javadoc, the reachability probe is mandatory (§4).

2. **Hosts by `host_mode`, as in C10/C10f, with every allowed candidate's file excluded.**
   - `host_mode = "1500"`: at least five other public classes of ≥ 1,500 lines exist. Draw the hosts with the recipe's seeded draw,
     `$PY $WM/scripts/mr_lib.py preview <key> <facade_rel> 5`, where `<facade_rel>` is the file of the facade you chose; the draw
     excludes that file. Record the drawn hosts and anchors in `host_notes`.
   - `host_mode = "largest5"`: your hosts are EXACTLY `hosts_hop_order` of the task record (the five largest public, non-interface,
     non-enum classes other than the allowed candidates' files, confirmed on the checkout; hop 1 in the largest, hop 5 = gold in the
     fifth). Anchors with `stageB_lib.pick_insertion_anchor` and the instance seed (C10F addendum §1). A listed host that cannot carry a
     public static method is replaced by the next-largest public class, recorded in `host_notes`.
   - Record `host_mode`, the five host sizes and the smallest host in the design docstring (covariates).

3. **Distinctness preferred.** Each allowed candidate carries `facade_planned_by`: the earlier task (batch 7 or 8) whose planned facade
   is the same method, or null. Prefer a candidate with `facade_planned_by = null` when it can carry the recipe validly; if only a
   planned-elsewhere candidate can, use it and say so (`facade_reuse_of` is recorded; it changes nothing in how you build).

Paths are the C10i paths (addendum §3): design `designs/<key>__i.py` (instance field `"<key>"`), `mr3_spec.py` → `specs/MI-<key>.json`,
`mr_validate.py` → `instances/MI-<key>/`, logs `logs/*MI-<key>*`, redesign archive `history/<key>__i/v1/`, scratch `/private/tmp/d4j-mi-<key>-*`.
Format examples (format only): `designs/Lang-31.py`, `designs/Compress-24.py` (static facades) and `designs/Codec-11__i.py`,
`designs/Lang-22__i.py` (batch-7 instance facades, V1) — do not reuse their method names.
