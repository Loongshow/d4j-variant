#!/bin/zsh
# PHASE 1 screening: checkout health, compile health, full-suite runtime and baseline failures, corpus statistics. Technical suitability only.
export PERL5LIB=$HOME/perl5/lib/perl5
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1/screening; PY=/opt/miniconda3/bin/python; mkdir -p $S
tmo() { $PY - "$@" <<'PY'
import subprocess,sys,time
t=int(sys.argv[1]); cmd=sys.argv[2:]; t0=time.time()
try: rc=subprocess.run(cmd,timeout=t).returncode
except subprocess.TimeoutExpired: rc=124
print(f"__RC={rc} __SECS={round(time.time()-t0)}")
PY
}
for P in "$@"; do
  BID=$(defects4j bids -p $P | head -1); D=$S/$P; rm -rf $D; echo "=== $P bug $BID start $(date -u +%FT%TZ) ==="
  t0=$(date +%s); defects4j checkout -p $P -v ${BID}f -w $D > $S/$P.checkout.log 2>&1; rc=$?; t1=$(date +%s); echo "$P checkout rc=$rc secs=$((t1-t0))"
  [ $rc -eq 0 ] || { echo "$P SUMMARY checkout_failed"; continue; }
  cd $D; SRC=$(defects4j export -p dir.src.classes 2>/dev/null | tail -1); TST=$(defects4j export -p dir.src.tests 2>/dev/null | tail -1); echo "$P dirs src=$SRC tests=$TST"
  C=$(tmo 1200 defects4j compile 2>&1 | tail -1); echo "$P compile $C"
  T=$(tmo 2400 defects4j test 2>&1 | tee $S/$P.fullsuite.log | tail -1); NF=$(grep -m1 "Failing tests:" $S/$P.fullsuite.log); echo "$P fullsuite $T | $NF"
  grep -E "^\s+- " $S/$P.fullsuite.log | head -20 > $S/$P.baseline_failures.txt
  NSRC=$(find $SRC -name '*.java' | wc -l | tr -d ' '); LSRC=$(find $SRC -name '*.java' -print0 | xargs -0 cat | wc -l | tr -d ' '); NTST=$(find $TST -name '*.java' | wc -l | tr -d ' ')
  BIG=$(find $SRC -name '*.java' -print0 | xargs -0 wc -l | awk '$1>=900 && $2!="total"' | wc -l | tr -d ' '); PUBSTAT=$(grep -rhE "^\s+public static [A-Za-z<>\[\], ]+ [a-zA-Z_]+\(" $SRC --include='*.java' | wc -l | tr -d ' '); PARAMDOC=$(grep -rh "@param" $SRC --include='*.java' | wc -l | tr -d ' '); NTESTM=$(grep -rhE "public void test|@Test" $TST --include='*.java' | wc -l | tr -d ' ')
  JV=$(grep -rhoE '(source|target)="[0-9.]+"' build.xml maven-build.xml pom.xml 2>/dev/null | sort | uniq -c | tr '\n' ' ')
  echo "$P corpus src_files=$NSRC src_lines=$LSRC classes_ge900=$BIG public_static_methods=$PUBSTAT param_docs=$PARAMDOC test_files=$NTST test_methods=$NTESTM javaversions=[$JV]"
  echo "$P SUMMARY bid=$BID checkout_secs=$((t1-t0)) compile=[$C] fullsuite=[$T] $NF end $(date -u +%FT%TZ)"
done
echo "=== screening finished $(date -u +%FT%TZ) ==="
