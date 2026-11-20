# The "no local trace" checklist (pre-specified construction rule, batch 3 onward)

Fixed on 17 October 2026, before any batch-3 instance is designed or run. Its sha256 is recorded in `AMENDMENTS.md` (W29). It must
not change while batch 3 is in progress.

It puts into operational form the rule the user approved on 17 October:

> "after the omission, every parameter and local variable is still read and updated, no sibling case is missing from an
> enumeration, and the gold's javadoc states no rule the code visibly breaks"

An independent review sharpened the wording before it was frozen (W29).

## What is checked

The checklist applies to the **gold method as it reads in the variant**: its javadoc, signature, body, inline comments and
identifiers.

A gold has a **LOCAL TRACE** if any one of T1, T2, T3 or T4 holds. A batch-3 instance is acceptable only if the gold has **no**
local trace.

Every item is judged from the gold's own text. You need quotable evidence, as set out under "How to apply it".

### T1: an input whose value cannot matter

The value passed for a parameter can never change the return value or any side effect, except by triggering an argument check (an
early return or a throw). T1 holds when the parameter:

- is never read;
- is read only after it has been overwritten on every path;
- is read only to compute dead locals (T2a); or
- is read only in argument checks (a null, emptiness, range or sign test that only returns early or throws) and takes no part in
  the main computation.

Examples:

- `useTransients` is declared but never consulted.
- `sep` is read only in `if (sep == null) throw new NullPointerException();` and is never appended.

### T2: a dead or frozen local, or a dead decision

A local variable of the gold, including a reassigned parameter, has a trace if it is in one of these states.

- **(a) Dead.** Follow its reads through other locals: they never reach the return value, a thrown exception, a call argument, or a
  write to an array, field or object. A local that is never read, read only to compute its own next value, or read only to compute
  other dead locals is dead.
  - Example: an accumulator `head` that is updated in the loop but dropped from the return.
  - A read in a condition that decides whether a live statement runs counts as reaching it; T2(c) covers decisions that cannot
    matter.
  - A write to a field is a side effect and is never T2(a).
- **(b) Frozen.** Either:
  - (i) it is initialised to a literal (`0`, `-1`, `false`, `true`, `null` or `""`) and never reassigned anywhere in the gold, yet
    it is returned, tested in a condition, or used as an index, position or count; or
  - (ii) inside a loop it serves as the loop's cursor, index, write position, count, flag or best-so-far, and no statement inside
    that loop assigns it.

  (ii) concerns only a variable that the loop is meant to move:
  - a cursor or write position whose unchanged value makes every iteration read or overwrite the same slot;
  - a counter meant to be incremented;
  - a flag meant to be set;
  - a best-so-far meant to be updated.

  It also applies to a field used as a loop cursor. A value computed before the loop and only read inside it is **not** frozen.
  Examples: a bound or length (`int n = a.length; for (int i = 0; i < n; i++)`), a base offset added to an advancing cursor, or a
  mode flag.

  Judge the role from how the code uses the variable, not from its name. Examples:
  - a write `index` passed to `arraycopy` that never advances;
  - an argmax `index` that is never assigned while the paired `largest` is;
  - `int pos = -1` returned after a search loop that never assigns it;
  - `boolean negative = false` tested but never set.

**(c) A dead decision.** An if/else branch, switch case or ternary whose outcome cannot change the result or any side effect. This
covers an empty or no-op branch, two branches with the same effect, and a test of a frozen local (b).

Example: `if (Character.isWhitespace(ch)) { } else if (!inWord) { ... }`.

### T3: a visibly incomplete set

T3 holds if you can quote one of the following.

**(a) Parallel siblings.** The gold gives the same kind of treatment to two or more members of a closed set, and another member of
that set gets none. The treatment can be its own case, branch, decode or check, or a term in a key, hash or comparison. Examples:

- segment types MOVETO, LINETO and CUBICTO are handled, but not QUADTO;
- there are branches for `letters && numbers` and for `letters`, but none for `numbers`;
- a key is built from three parameters, but not from a fourth that the gold also reads.

**(b) One of two.** The set has exactly two members with the same role, and the gold handles one but not the other. Two-member sets
include:

- the halves of a pair: high and low surrogate, real and imaginary part, key and value;
- the two ends of a range: start and end index, lower and upper bound, from and to;
- the two JSON Pointer escapes `~0` and `~1`.

Examples:

- the start index is clamped to 0, but the end index is never clamped to the length;
- `~0` is decoded but `~1` is not.

**(c) A named class handled only in part.** The gold's own text (javadoc, a name, a message or a comment) names a class, and the
gold handles only part of it. Example: the javadoc says "the finite entries", and the gold rejects `isInfinite` entries but lets
NaN through.

**(d) Mentioned but untreated.** The gold reads a member or field but does not give it the treatment its sibling gets. Examples:

- it checks that the second half of a pair exists, but never compares it;
- it hashes a field that it never compares.

**Closure rule.** A set is closed only if its members are fixed by one of:

- the gold's own text: its parameters, the flags it tests, the parts or fields it reads;
- a Java type it uses: an enum, or a type code such as `PathIterator.SEG_*`;
- a format or standard that the gold's own text names, such as "JSON Pointer", "Java string literal" or "CSV".

The two-member sets in (b) are also closed. Do not bring in a member list from a format or convention that the gold does not name.
The special values of `float` and `double` (NaN, +infinity, -infinity, -0.0) are **not** a closed set unless the gold's own text
names the class, for example "finite".

**Not T3** (judged on the variant text):

- **No member handled.** No member of the set is handled at all. Examples: a sum with no special-value test, a join with no null
  test, an identifier check with no reserved-word test, a word loop with no reset.
- **One member of a larger unnamed set.** Exactly one member of a set of three or more is handled, and the gold does not name the
  class. Example: a sum whose only special-value test is a NaN skip.
- **Argument checks.** Argument checks or normalisations of parameters (null, empty, range) do not form a set with per-element
  special values. An element-level skip is judged only against other element-level treatments.

### T4: the gold's own text contradicts its code

T4 holds if you can quote both of the following.

- **(i) A phrase that names something concrete.** It appears in the gold's javadoc (including its `@param`, `@return` and `@throws`
  clauses), in an inline comment, or in one of its identifiers, and it names a concrete rule, limit, bound, value class, case or
  property. Examples:
  - "at most 10,000";
  - "the finite entries";
  - "may be null" (the method must accept null without throwing);
  - "not null";
  - "@throws IllegalArgumentException if the array is empty";
  - a local named `finiteSum`.
- **(ii) The place in the body where that item is visibly not met.** Either no line tests, enforces or produces it, or a path does
  what the phrase excludes. Example: under "not null", it returns the literal `null`, or a local that still holds its `null`
  initialiser.

Judge (ii) by matching the quoted phrase against the code, for the case the phrase itself names. Do not construct other inputs.

**Not T4: a caller precondition on a parameter.** Examples: "@param dataset the dataset (null not permitted)", "@param str ...,
not null", "must be positive". Such a phrase says what the caller must supply, not what the gold does. It is T4 only if the gold's
text says the gold itself checks or handles that case, for example "@throws NullPointerException if ..." or "a null array is
treated as empty".

**Not T4:** a description of what the method computes in general that lines of the body do address. Examples: "the index of the
first match at or after start", "the reduced fraction", "joins the elements", "a valid variable name". This holds even if you can
construct an input (a negative start, an overflow, an empty array) on which the code does not deliver it.

## How to apply it

1. Read only the gold method in the variant: its javadoc, signature, body, comments and identifiers. No test, no result, no other
   method.
2. For each of T1, T2, T3 and T4, answer `present` or `absent`.
   - Mark an item `present` only if you can quote text from the gold that meets that item's test.
   - For something missing, quote the declaration or the handled siblings and name the missing member.
   - If you can quote such text but are unsure whether it meets the test, mark `present` and explain; that doubt counts as a trace.
   - A suspicion that the method mishandles some input, with nothing in its text that meets an item's test, is `absent`.
3. The verdict is **NO_TRACE** if all four items are absent, and **TRACE** otherwise.

## How it is used in batch 3

- **Builders.** Every batch-3 builder must make the **whole** variant gold pass T1 to T4, not only the effect of the omitted line.
  Before choosing the omission, the builder applies the checklist to the correct gold too and rewrites any pattern it already
  shows. The builder records an item-by-item self-check in the design docstring and in its result.
- **Independent checker.** A checker that is neither the builder nor the auditor applies the checklist blind, to the variant gold
  text only (`construction/mainrun/TRACE_CHECK_BRIEF.md`). If it returns TRACE, the instance gets the single pre-run redesign
  defined in `main-run/BATCH3_PREREGISTRATION.md`.
- **Other validity rules are unchanged:** the 16 gates, the quiet gold, the single owner, the single existing trigger, the external
  pins and the leakage rules.
- **The ownership audit is unchanged.** CONFIRMED is required for an instance to be counted. FLAG_AMBIGUOUS instances are run and
  reported separately, as in `AUDIT_BRIEF.md`.

## Provenance of the examples

Some examples (QUADTO, `~1`, the `letters`/`numbers` branches, the cache key, "finite entries", the second half of a pair) were
drawn from batch-1 and batch-2 golds after their results were known. Any retrospective classification of those golds under this
checklist is therefore not independent of how the rule was written. Only batch 3, built under the rule before any run, tests it.
