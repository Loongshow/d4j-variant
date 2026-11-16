# MATH_SUPPLEMENTARY_PROTOCOL_NOTE — recorded BEFORE launching the Math supplementary block (2026-09-23, ≈ 07:00 UTC)

## 1. What is being launched

`MATH-NORM-CONTROL-01` run-006…010 and `MATH-NORM-TREATMENT-01` run-006…010 (five + five), one run at a time, through the same frozen server (`diagnostic-noncanonical-v3`, port 8792, pid 85522), same agent profile (`mini-swe-agent-openai-gpt-5-6`, mini-swe-agent 2.4.6, gpt-5.6), same prompt (`d4j-localization-only/v2`), same budget (50 calls / 5 test runs / 300 s / 30 s startup), same packages (byte-identical, hashes in `analysis/package_hashes.txt`; server status `validated`), same scoring. run-001…005 of both targets stay untouched. The only launcher change is `MP_MAX_RUNS=10` (slot limit for this user-instructed supplement); launcher sha256 recorded in `diagnostic/launcher_supp_*.log`.

## 2. Pre-launch verification

- Server/root/model/provider: `/api/env` reports the v3 root, `openai/gpt-5.6`, `credential_source: D4J_OPENAI_API_KEY`, `provider_ready: true` (name only; no value inspected). Variants `MATH-NORM-CONTROL-01` / `MATH-NORM-TREATMENT-01` discovered.
- Supplementary slots run-006…010 are empty for both targets.
- Protected/canonical trees: inventory of the whole v3 root (105 748 files) identical to the post-block inventory (0 removed / 0 changed / 0 added); the launcher preflight re-checks the protected trees before each launch.
- Provider health: three bounded smoke probes two minutes apart (`diagnostic/probe_supp_{1,2,3}.json`), then a single canary run; launches continue one at a time and pause after any stall.

## 3. Directory-traversal exposure under the frozen protocol (documented before launch)

The frozen harness runs mini-swe-agent as the same user as the server with cwd = the workspace, and the agent writes its own `cd <absolute path> &&` prefix; the prompt prints the workspace's absolute path, from which parent paths are derivable. The environment class filters nothing but the submit tool. Reachable in principle (same filesystem user):

| Path | Content that would matter | Historical access (20 first-block runs, raw scan `analysis/data/out_of_workspace_scan_block1.json`) |
|---|---|---|
| own run dir `../../` | `method_catalog.json` (class/method/file/line spans — no gold marker); `workspace_manifest.json` — its `variant_patch_results.stdout` lists the files touched by the variant patch (the five hop files for TREATMENT, the facade file for CONTROL); `task.json`, `prompt.txt`, config (no gold labels) | `method_catalog.json` read once (Chart TREATMENT run-005 call 21, after the gold was on screen); `workspace_manifest.json` never opened |
| sibling run dirs of the same target | `evaluation.json`, `ranking.json`, `fault-localization-submission.json` of earlier runs = the answer | listed by name in two runs (Chart CONTROL run-005, Chart TREATMENT run-005); never opened |
| other targets' run dirs, `_smoke/` | other variants' gold labels | never accessed |
| `new_bug_variants/<P>/bug-1/L20/<ID>/` | `variant.patch` = the fault diff; `variant_manifest.json` = gold labels | never accessed |
| `workspaces/defects4j/Math-1/fixed` | unpatched reference checkout (a `diff -r` would expose every changed line) | never accessed |
| `.defects4j.config`, `defects4j.build.properties` (inside the workspace) | Defects4J pid/vid and the real Chart-1/Math-1 bug's build properties — nothing about the synthetic fault | read in Chart TREATMENT run-004 (and one Lang branch run earlier) |

## 4. Isolation correction: designed, not applied

A purely permission-based lock (chmod 000 on sibling run dirs, the four package dirs, the fixed checkout and the current run's `workspace_manifest.json` for the duration of the agent process; store code verified to hold gold labels and the prepared workspace in memory during execution, run listings tolerate unreadable entries) was designed and its dry test attempted; the session's tool-permission classifier denied the chmod on the shared server root ("Modify Shared Resources"), and no workaround was attempted. Consequently **the supplementary block runs under the unchanged historical protocol** — which is also the condition that keeps run-006…010 exactly comparable with run-001…005 and with Chart and Lang.

## 5. Preregistered contamination rule for run-006…010

After the block, `scripts/scan_out_of_workspace.py` is run on every new trajectory. A run is **contaminated** if any tool OUTPUT displays the *content* of a sibling run artifact (rankings, evaluations, submissions), a package file (patch, manifest), the fixed reference checkout, or its own `workspace_manifest.json`. A contaminated run is preserved, reported with its trajectory, and **excluded from rank and navigation metrics** (like a timeout, it is not a localization outcome). Reading the own-run `method_catalog.json` or Defects4J build metadata, or listing file names without opening them, is recorded as a protocol observation but is not contamination (no gold information). The rule is fixed before any supplementary run starts.

## 6. Recommendation to the supervisor (not executed here)

Close the gap in the harness: run the agent with a cwd whose ancestors do not expose the run tree (e.g., a per-run temporary root with the workspace copied in and nothing else), stop printing the absolute run path in the prompt (a versioned prompt change), and keep the raw-trajectory scan as a standard post-run check.
