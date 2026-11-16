#!/bin/zsh
# Resume the Level-B run programme once Anthropic credits exist. Idempotent: (re)starts any server that is not listening, re-proves the
# runner environment for restarted servers, probes once (bounded), then launches the frozen blocks. Usage:
#   scripts/resume_after_credits.sh sonnet     -> 50 Sonnet runs (5 pairs x 2 arms x 5) on sonnetA/sonnetB, then automatic stall top-ups
#   scripts/resume_after_credits.sh opus       -> 18 Opus runs (3 pre-registered pairs x 2 arms x 3) on opusA, then automatic top-up
#   scripts/resume_after_credits.sh pilot      -> the differential pilot (18 Sonnet + 6 Opus) in ocflb-differential-analysis-v1
set -u
SP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs; L=$SP/ocflb-level-b-v1; PY=/opt/miniconda3/bin/python; cd $L
export PERL5LIB=$HOME/perl5/lib/perl5
set -a; . $SP/.env; set +a       # ANTHROPIC_API_KEY only; never echoed
what=${1:-sonnet}
if [ "$what" = pilot ]; then exec $SP/ocflb-differential-analysis-v1/scripts/run_pilot.sh; fi
ensure() {   # ensure <model-id> <port> <root-name>
  if lsof -nP -iTCP:$2 -sTCP:LISTEN >/dev/null 2>&1; then echo "$3 already listening on $2"; return; fi
  scripts/start_server.sh $1 $2 $3; sleep 6
  case $3 in opus*) PID=$(cat diagnostic-opus/server_$3.pid);; *) PID=$(cat diagnostic-sonnet/server_$3.pid);; esac
  scripts/prove_runner_env.sh $PID $L/construction/fresh/chart01/Chart org.jfree.chart.plot.junit.PiePlotTests::testEquals review/RUNNER_ENV_PROOF_$3.md || { echo "runner proof FAILED for $3"; exit 3; }
}
case $what in
  sonnet) ensure claude-sonnet-4-6 8821 sonnetA; ensure claude-sonnet-4-6 8822 sonnetB
          $PY scripts/probe_model.py 8821 sonnetA 90 || { echo "probe failed (credits?) - nothing launched"; exit 2; }
          $PY scripts/launch_runs.py sonnet
          for s in sonnetA sonnetB; do nohup sh scripts/topup_after.sh $(cat diagnostic-sonnet/driver_$s.pid) $s > /dev/null 2>&1 & done
          echo "Sonnet block launched; monitor: tail -f diagnostic-sonnet/driver_sonnetA.out diagnostic-sonnet/driver_sonnetB.out; then: sh scripts/finalize_lb.sh";;
  opus)   ensure claude-opus-5-5 8823 opusA
          $PY scripts/probe_model.py 8823 opusA 90 || { echo "probe failed (credits?) - nothing launched"; exit 2; }
          $PY scripts/launch_runs.py opus
          nohup sh scripts/topup_after.sh $(cat diagnostic-opus/driver_opusA.pid) opusA > /dev/null 2>&1 &
          echo "Opus block launched; monitor: tail -f diagnostic-opus/driver_opusA.out; then: sh scripts/finalize_lb.sh";;
  *) echo "usage: $0 sonnet|opus|pilot"; exit 1;;
esac
