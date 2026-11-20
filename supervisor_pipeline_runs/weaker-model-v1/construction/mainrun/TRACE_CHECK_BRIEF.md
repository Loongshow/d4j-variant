# Trace-check brief (one independent checker per gold)

You apply the pre-specified checklist `construction/mainrun/NO_LOCAL_TRACE_CHECKLIST.md` to ONE gold method. Read the checklist
first, completely. Its text governs; this brief only tells you how to work.

## Input

You are given the gold method's text as it reads in the variant: its javadoc, signature and body. You get it either inline or as
the output of `scripts/mr_gold_text.py MR-<key>`, which prints only that method. You are given nothing else.

- Do not open any other file except the checklist.
- Do not read designs, specs, audits, tests, results, run outputs, reports or other instances.
- No network, no model or API calls, and never open `.env` files.
- Do not edit any file.

## Task

For each of T1, T2, T3 and T4, decide `present` or `absent` exactly as the checklist defines it.

- Do not guess what the method should do from outside knowledge. Use outside knowledge only as far as the checklist's T3 closure
  rule allows.
- Mark an item `present` only if you can quote text from the gold that meets that item's test.
  - For something missing, such as an unused parameter or a left-out member, quote the declaration or the handled siblings and name
    what is missing.
  - If you can quote such text but are unsure whether it meets the test, mark `present` and explain; that doubt counts as a trace.
  - A suspicion that the method mishandles some input, with nothing in its text that meets an item's test, is `absent`.

## Verdict and output

- `NO_TRACE`: T1, T2, T3 and T4 are all absent.
- `TRACE`: otherwise.

Return only the structured result:

- for each of T1–T4: the status, the quote (empty if absent) and one sentence on why;
- the verdict.
