# Exposure and identification annotation guide (W72, exploratory)

You annotate agent runs from a fault-localization study. In each run, an LLM agent (gpt-5.5) was given a failing test in a Java
repository and had to rank ten methods by how likely they are to contain the fault. One method, the **gold**, contains an
injected one-line omission. The method the failing test calls is the **facade**.

For each run `Rxx` you have exactly three files in `views/Rxx/`:
- `gold_spec.md`: the gold method, its file, the omitted text, and the gold's code with the edited region marked `>>`.
- `agent_text.md`: the agent's commands, each output's number and size, its final ranking and its final evidence chain. (The agent's
  hidden reasoning is not available; its visible text is usually empty, so the evidence chain is its own account.)
- `tool_outputs.txt`: every tool output in full, numbered `### output #k`. It is long: search it (grep for distinctive text of the
  marked lines, for the gold method's name or file name) rather than reading it end to end.

Rules: open only these files. Do not open any other file in the repository (no CSV, JSON, scripts, results or other runs), do not
run anything except reading/searching these files, and do not discuss runs with anyone. Answer from the evidence in the files.

## Questions

**Q1 exposed_at_location** — Did any tool output display the marked (`>>`) line(s) as part of the gold method in the gold's file?
- `yes`: an output shows the gold's file content covering the marked line(s) (e.g. `cat`, `sed -n`, `nl`, `grep -A/-B` context of
  that file), recognisably within the gold method. Line-number prefixes and grep prefixes do not matter.
- `no`: no output shows the marked lines of the gold's file. Identical text shown only from another file or method does not count.
- `unclear`: you cannot decide (say why in notes).
Give the output number(s) where it first appears.

**Q2 gold_body_seen** — How much of the gold method's body was displayed in outputs? `most` (about 90% or more), `partial`, `none`.

**Q3 fault_identified** — In the agent's own words (visible text, if any, and the final evidence chain), is the fault identified?
- `yes`: the agent states that the wrong value or behaviour arises in the gold method because of the missing check/step, or names
  the specific missing condition (or an equivalent description of the defect at the gold).
- `partly`: the agent names the gold as involved, suspicious or producing the wrong value, without identifying the missing step.
- `no`: the gold is not discussed as a source of the failure.
Quote the decisive words (at most 40 words).

**Q4 rank1_reason** — Only if the gold is NOT ranked first in the final submission (otherwise `NA`). What main reason does the
agent give for the method it ranked first?
- `ROLE`: it is the method under test / the API the test calls / the entry point.
- `FIX_SITE`: it is where the fix or modification should go.
- `DOC`: it violates or does not implement its documentation / described algorithm.
- `CHAIN_ORDER`: upstream / call order ranking without further reason.
- `OTHER` (explain) or `UNCLEAR` (no reason given).
Quote the decisive words (at most 40 words).

## Output

Write one JSON file (path given in your task) containing a list with one object per run, in this exact shape:
`{"rid": "R01", "q1": "yes|no|unclear", "q1_outputs": [9], "q2": "most|partial|none", "q3": "yes|partly|no", "q3_quote": "...",
"q4": "ROLE|FIX_SITE|DOC|CHAIN_ORDER|OTHER|UNCLEAR|NA", "q4_quote": "...", "notes": "..."}`
