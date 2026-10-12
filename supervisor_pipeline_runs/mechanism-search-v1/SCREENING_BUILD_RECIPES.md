# Screening build recipes (written 2026-10-10, before any new prototype is built or run)

Every new screening prototype is one validated single-fault variant of a Defects4J fixed version (`bug-1` base), built with
`scripts/mx_build_validate.py` and accepted only when READY. All prototypes are EXPLORATORY.

## Rules for every recipe

- **The fault** is one small semantic change inside one existing production method (the gold). The minimal repair restores
  exactly that method.
- **Context edits** are allowed only if behaviour-preserving: the CORRECT configuration (context edits plus tests, no fault)
  passes the full suite (G1). Every competing method must stay correct, unchanged or proven equivalent.
- **The trigger test** is new, neutral and deterministic. It exercises public behaviour. Its method name is neutral: no gold or
  competitor method name, and no fault vocabulary. Expected values should be compatible with more than one candidate where the
  mechanism calls for it.
- **The task must stay objectively solvable.** Decisive evidence for the gold exists in the repository: code, a contract, a
  second caller, a passing test or an inverse operation. It may be far from the gold, but it is never removed.
- **Declarations:** the gold, the competing methods (decoys), entry points, decisive-evidence locations, a one-paragraph
  ownership reason, and at least one one-line competitor edit for the owner-invariance gate (G9).
- **Projects:** prefer Lang, Math, Compress and JacksonCore. Chart only where no alternative exists.

## Families to build (one prototype each; a second only if the first cannot be validated)

| Recipe | Family | Project | Construction |
|---|---|---|---|
| R1 | M1 + M6 local oddness | Lang | A correct method on the trigger path, written in a valid but unusual form (an unusual boundary rule, sentinel or subtraction order), already present or produced by a proven-equivalent context edit. The gold has a quiet omission, for example a missing normalisation step. |
| R2 | M2 omission | Compress | The gold drops one necessary step (a mask, sign handling or a state update) and its remaining body reads as complete. No competitor is made odd. This is the pure omission control. |
| R3 | M3 definer vs adapter | Math | A definer returns a value whose convention looks unusual but is fixed by its javadoc and a passing unit test. The adapter consuming it omits the required conversion (the gold). |
| R4 | M4 multiple plausible owners | Math | A 3-stage computation (e.g. parse or normalise, convert, format), any stage of which could plausibly own the observed behaviour. The fault is in one stage; decisive evidence is a passing test or second caller elsewhere. |
| R5 | M7 inverse pair | Lang or Compress | An encode/decode pair (escape/unescape, write/read). The correct side contains a legitimately asymmetric step. The fault is a subtle omission on the other side. A round-trip trigger whose failure fits either side. |
| R6 | M8 cross-caller convention | Lang | One callee used by two callers. The trigger's caller makes one reading of the callee natural; the second caller, covered by existing passing tests, fixes the real reading. The fault is in the trigger's caller (the gold). |
| R7 | M10 entry-point | Math | A public entry method with visible validation and branching; the gold is one or two calls below. The trigger observes only public behaviour. |
| R8 | M12 same-file competition | Lang | The gold and a correct competitor in the same large source file, both executed by the trigger, both plausibly responsible. |
| R9 | M13 cross-file competition | Lang or Compress | Like R8, but the competitor is in a different class that the test touches directly (easier to find); the gold needs one call to be followed. |
| R10 | M14 state propagation | Compress or Lang | The gold writes a field or accumulator incorrectly; the failure is observed later, in a more complex reader method (a competitor). |
| R11 | M15 fallback path | Lang or Math | The fault is only on a default or fallback branch; the normal branch is correct and prominent. The trigger reaches the fallback through public behaviour. |
| R12 | M17 type-semantic | JacksonCore or Lang | An inclusive/exclusive or index/count confusion where the representation permits both readings. The correct reading is fixed by a contract or passing test elsewhere. |
| R13 | M9 test ambiguity | Lang or Math | The failure signature (a boolean or aggregate assertion) is compatible with two or three suspects; the test names no method. |

These recipes cover 13 families beyond those with re-hosted prototypes (M2, M3, M5, M9, M11, M16, M17, M19, M20), so more than 12
families reach behavioural screening.
