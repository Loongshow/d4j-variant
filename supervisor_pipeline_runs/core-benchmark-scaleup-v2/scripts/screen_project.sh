#!/bin/zsh
# Infrastructure screening of one Defects4J project (P1-P4, P9): checkout 1f, compile, time the full suite, measure source size.
# Usage: screen_project.sh <Project> [bugid]
export PERL5LIB=$HOME/perl5/lib/perl5
D=/Users/shawnli/Desktop/Honours/defects4j; S=$D/supervisor_pipeline_runs/core-benchmark-scaleup-v2; P=$1; B=${2:-1}; W=$S/screening/$P; LOG=$S/screening/${P}_screen.log
{ echo "== $P (bug $B f) screening $(date -u +%FT%TZ)"
  rm -rf $W; t0=$(date +%s)
  defects4j checkout -p $P -v ${B}f -w $W > $S/screening/${P}_checkout.log 2>&1 && echo "checkout: OK ($(($(date +%s)-t0)) s)" || { echo "checkout: FAIL"; tail -5 $S/screening/${P}_checkout.log; exit 1; }
  SRC=$(cd $W && defects4j export -p dir.src.classes 2>/dev/null | tail -1); TST=$(cd $W && defects4j export -p dir.src.tests 2>/dev/null | tail -1)
  echo "src dir: $SRC | test dir: $TST"
  t0=$(date +%s); (cd $W && defects4j compile > $S/screening/${P}_compile.log 2>&1) && echo "compile: OK ($(($(date +%s)-t0)) s)" || { echo "compile: FAIL"; grep -E "error|ERROR" $S/screening/${P}_compile.log | head -5; exit 2; }
  echo "java files: $(find $W/$SRC -name '*.java' 2>/dev/null | wc -l | tr -d ' ') | test files: $(find $W/$TST -name '*.java' 2>/dev/null | wc -l | tr -d ' ') | src LOC: $(find $W/$SRC -name '*.java' -exec cat {} + 2>/dev/null | wc -l | tr -d ' ')"
  echo "CRLF sources: $(find $W/$SRC -name '*.java' -exec file {} + 2>/dev/null | grep -c CRLF)"
  t0=$(date +%s); /opt/miniconda3/bin/python -c "
import subprocess,sys
try:
    r=subprocess.run(['defects4j','test'],cwd='$W',capture_output=True,text=True,timeout=1500); print(r.stdout[-500:]); sys.exit(0)
except subprocess.TimeoutExpired: print('SUITE TIMEOUT >1500s'); sys.exit(3)" > $S/screening/${P}_test.log 2>&1; rc=$?
  echo "full suite: rc=$rc ($(($(date +%s)-t0)) s) | $(grep -E 'Failing tests|SUITE TIMEOUT' $S/screening/${P}_test.log | head -2 | tr '\n' ' ')"
  echo "== $P done $(date -u +%FT%TZ)"; } > $LOG 2>&1
