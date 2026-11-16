#!/bin/zsh
# Differential pilot (Part 9): Sonnet 3 runs on each of CF-V1..V5 (15) plus 3 V0 anchor runs on ADV-DEFINER-01 (18 = the Sonnet cap), then Opus 3 runs on CF-V3 and CF-V5 (6). Run only when credits exist.
set -u; D=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-differential-analysis-v1; cd $D
set -a; . ../.env; set +a
scripts/start_server.sh claude-sonnet-4-6 8811 sonnetCF; scripts/start_server.sh claude-opus-5-5 8812 opusCF; sleep 5
scripts/prove_runner_env.sh $(cat diagnostic/server_sonnetCF.pid) $D/construction/Chart org.jfree.chart.plot.junit.PiePlotTests::testEquals $D/diagnostic/RUNNER_ENV_PROOF_sonnetCF.md
/opt/miniconda3/bin/python scripts/probe_model.py 8811 sonnetCF 60 || { echo "probe failed (credits?)"; exit 2; }
/opt/miniconda3/bin/python scripts/cf_driver.py --model sonnetCF --variants ADV-DEFINER-01,CF-V3,CF-V5,CF-V1,CF-V2,CF-V4 --planned 3   # V0 anchor first, then the two decisive conditions, then the rest
/opt/miniconda3/bin/python scripts/cf_driver.py --model opusCF --variants CF-V3,CF-V5 --planned 3
/opt/miniconda3/bin/python scripts/cf_metrics.py && echo "pilot done; see COUNTERFACTUAL_RESULTS.md after running scripts/build_cf_results.py"
