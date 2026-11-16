# Addendum (2026-09-27): the pilot's Claude agents could not execute `defects4j test`

Found during the adversarial root. Every `defects4j test` issued by a Claude agent in this pilot returned
`Can't locate String/Interpolate.pm in @INC` because `scripts/start_pilot_server.sh` does not export `PERL5LIB`; the frozen GPT-5.6
runs it was compared with executed their tests through ant. `ANTHROPIC_MODEL_SELECTION.md` / the comparability verdict
NEAR_EQUIVALENT therefore overstate equivalence in one respect: repository access, prompt, budgets and parser were identical, the
executable test was not. Claude's ranks in the pilot were reached without a working test command. No pilot artifact is modified by
this note. Details and the bounded validity check: `../adversarial-break-v1/diagnostic/PROTOCOL_DEVIATION_TEST_RUNNER.md`.
