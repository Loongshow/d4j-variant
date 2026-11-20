# Batch 7 (cell C10i, the paired static/instance bridge) addendum to the builder brief

You build a **C10i** instance: the C10 recipe with an **instance-method facade**, on a bug that already has a C10 or C10f instance with a
static facade. The pair (same fixed revision, same hosts where the draw allows, different facade kind) is the pre-registered comparison of
`main-run/BATCH7_PREREGISTRATION.md`. `BUILD_BRIEF.md` applies in full with its "batch 3" rules (no-local-trace HARD rule, pre-run checks and
single redesign, redesign archive); where your bug's hosts are the five largest classes, `BUILD_BRIEF_C10F_ADDENDUM.md` §1 applies to the
hosts. Your pre-registration is `BATCH7_PREREGISTRATION.md`.

## 1. The facade is an instance method; the hops stay public static

The facade is one of the allowed instance methods of your task record. Its body becomes a guard (if the original had one) plus **state
gathering and one call to hop 1**; hop 1 → … → hop 5 are new `public static` methods in the five hosts, hop 5 the gold, exactly as in C10.
Use the smallest variant that carries the method's computation, and record which in the design docstring (`facade_variant`):

| Variant | When | How |
|---|---|---|
| **V1 state as parameters** | the method reads fields (and writes at most one) | the facade reads the fields it needs (it is inside the class, so private fields are fine) and passes the values to hop 1; the chain computes; the facade returns the result and, if the original assigned a field, writes the returned value back |
| **V2 receiver as parameter** | the computation needs the object's public methods | pass `this` to hop 1 (typed as the declaring class or an interface it implements); hops call its public methods only |
| **V3 same-package hosts** | the computation needs package-private types or members | only if the task record lists `same_pkg_hosts`; otherwise V5 |
| **V4 pre-compute private helpers** | the computation calls private methods of its class | call them in the facade and pass the results down (the facade keeps that much computation; say so); never copy private logic into a hop |
| **V5 generic hops** | values of package-private types must pass through hops in other packages | hops are generic methods (`<T>`) that carry the values without naming the types; the step that creates or reads such values stays in the facade or in a same-package hop |

**Not allowed** (each is a tell or an API change): widening the visibility of any existing member or type; adding a new class, interface or
nested type; reflection; changing the facade's signature, modifiers, overrides or thrown types; editing any test.

The gold is still a quiet one-line omission in hop 5 (BUILD_BRIEF fault rules and the checklist T1–T4), and the facade lie is still appended
to the facade's javadoc (if the facade has no javadoc, add a one-sentence javadoc in the class's own voice first, as JacksonDatabind-103 did).

## 2. Independence from the static instance

The bug already has a static-facade instance. Do **not** open its design, spec, patches, audit or any file under `instances/MR-<key>/`,
`construction/mainrun/designs/<key>.py`, `construction/mainrun/audits/MR-<key>.json` or `construction/mainrun/history/<key>/`. Your facade
is a different method (the task record guarantees it); your hop and gold method names must not reuse that instance's names, which you do
not know. The fixture `construction/fresh-mr/<key>` is the same pristine checkout and is read-only.

## 3. Names and paths for this cell

- Design: `construction/mainrun/designs/<key>__i.py` (the `__i` suffix keeps it apart from the static design).
- Spec and instance: `mr3_spec.py` writes `construction/mainrun/specs/MI-<key>.json` and `mr_validate.py` builds `instances/MI-<key>/`.
  Run `$PY $WM/scripts/mr3_spec.py $WM/construction/mainrun/designs/<key>__i.py C10 --check`, then
  `$PY $WM/scripts/mr_validate.py $WM/construction/mainrun/specs/MI-<key>.json > $WM/construction/mainrun/logs/validate_MI-<key>.log 2>&1`.
- Logs: `construction/mainrun/logs/*MI-<key>*`; redesign archive `construction/mainrun/history/<key>__i/v1/`.
- The design's `instance` field is still `"<key>"` (it names the fixture and the seed); `mr3_spec.py` adds the `MI-` prefix itself.

## 4. Reachability probe (mandatory, as in C10f)

Before designing, make the facade throw `IllegalStateException("PROBE-REACHED")` in a scratch copy, run its candidate trigger tests, and
confirm that an existing test fails with that message. Record the probe in the design docstring and in your result. If no existing test
reaches any allowed facade, report UNBUILDABLE.

## 5. What to return

The structured result of `BUILD_BRIEF.md`, plus `facade_variant` (V1–V5, possibly several), `state_passed` (the fields or receiver handed to
hop 1, and any write-back), `host_mode`, the five host sizes and the reachability probe result.
