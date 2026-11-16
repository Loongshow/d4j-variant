#!/bin/zsh
# Rebuild + revalidate + package + docs + packets for one Level-B pair (revision cycle). Usage: rebuild_pair.sh <key> <Project> <bug-XX> <PAIR_ID> <rev>
set -u
L=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/ocflb-level-b-v1; PY=/opt/miniconda3/bin/python
key=$1; P=$2; bug=$3; ID=$4; rev=$5; PD=$L/projects/$P/$bug; export PERL5LIB=$HOME/perl5/lib/perl5
echo "[$(date -u +%FT%TZ)] rebuild $ID revision $rev"
# archive the previous revision's record (never delete evidence)
if [ -f $PD/pair.json ]; then mkdir -p $PD/rev$((rev-1)); cp $PD/pair.json $PD/rev$((rev-1))/pair.json; [ -f $PD/validation/validation.json ] && cp $PD/validation/validation.json $PD/rev$((rev-1))/validation.json; [ -f $PD/validation_run.log ] && cp $PD/validation_run.log $PD/rev$((rev-1))/validation_run.log; [ -d $PD/blindness ] && mv $PD/blindness $PD/rev$((rev-1))/blindness; fi
for arm in DEFINER ADAPTER; do d=$L/new_bug_variants/$P/bug-1/L20/$ID-$arm; [ -d $d ] && rm -rf $d && echo "removed installed $d (revision $((rev-1)))"; done
$PY $L/scripts/pairs/build_lb_$key.py $L/construction/work/$key/$P || { echo "BUILD FAILED"; exit 1; }
$PY $L/scripts/ocflb_validate.py $PD/pair.json $L/construction/work/$key/$P $L/construction/fresh/$key/$P > $PD/validation_run.log 2>&1; tail -n 3 $PD/validation_run.log
grep -q "overall: READY" $PD/validation_run.log || { echo "NOT READY: $ID"; exit 2; }
$PY $L/scripts/ocflb_package.py $PD/pair.json && $PY $L/scripts/ocflb_docs.py $PD/pair.json && $PY $L/scripts/blindness_packets.py $PD/pair.json $L/construction/blind/$P
echo "[$(date -u +%FT%TZ)] $ID revision $rev READY, packaged, documented, packets written"
