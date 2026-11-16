#!/bin/zsh
# FIVE-state semantic-equivalence probe for one camouflage pair:
#   original        = pristine construction checkout (no patch)
#   low_buggy       = LOW reproduction checkout  (packaged patches, bug in the gold)
#   high_buggy      = HIGH reproduction checkout (packaged patches, bug in the gold)
#   low_correct     = copy of low_buggy  with the gold line restored
#   high_correct    = copy of high_buggy with the gold line restored
# Asserts: low_correct == original == high_correct on every case (the chain refactor is behaviour
# preserving in both hosts), low_buggy == high_buggy on every case (the two arms are semantically
# identical: A4 "semantic difference = 0"), and original != low_buggy on at least one case.
# Usage: equivalence_probe_camo.sh <spec> <D4J project> <ProbeClass>
export PERL5LIB=$HOME/perl5/lib/perl5; PY=/opt/miniconda3/bin/python
R=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/camouflage-model-comparison-v1
C=$R/experiment-a-camouflage/construction; A=$R/experiment-a-camouflage; E=$A/equivalence
S=$1; D4J=$2; CLS=$3
LOW=$($PY -c "import json;print(json.load(open('$C/configs/$S/pair_config_low.json'))['treatment_id'])")
HIGH=$($PY -c "import json;print(json.load(open('$C/configs/$S/pair_config_high.json'))['treatment_id'])")
mkdir -p $E/$S
restore() { # <arm-config> <src-checkout> <dst-checkout>
  rm -rf $3; cp -R $2 $3
  $PY - "$1" "$3" <<'PYX'
import json,sys
cfg=json.load(open(sys.argv[1])); A=cfg["treatment"]; p=sys.argv[2]+"/"+A["gold_file"]
raw=open(p,"rb").read().decode(); eol="\r\n" if "\r\n" in raw else "\n"; t=raw.replace("\r\n","\n")
assert t.count(A["bug_line"])==1, t.count(A["bug_line"])
open(p,"wb").write(t.replace(A["bug_line"],A["orig_line"],1).replace("\n",eol).encode())
print("gold line restored in", sys.argv[2].split("/")[-1])
PYX
  GF=$($PY -c "import json;print(json.load(open('$1'))['treatment']['gold_file'])")
  GN=$(basename $GF .java); GD=$(dirname $GF | sed -e 's#^src/main/java/##')
  for d in build target/classes; do [ -d $3/$d/$GD ] && find $3/$d/$GD -maxdepth 1 \( -name "$GN.class" -o -name "$GN\$*.class" \) -delete; done
  (cd $3 && defects4j compile > $E/$S/compile_$(basename $3).log 2>&1 && echo "recompiled $(basename $3)")
}
run() { # <checkout> <name>
  CP=$(cd $1 && defects4j export -p cp.test 2>/dev/null | tail -1)
  mkdir -p $E/$S/build_$2
  javac -cp "$CP" -d $E/$S/build_$2 $E/$CLS.java 2> $E/$S/javac_$2.log && \
  java -cp "$CP:$E/$S/build_$2" $CLS > $E/$S/out_$2.txt 2> $E/$S/java_$2.log
  echo "$2: $(wc -l < $E/$S/out_$2.txt) cases"
}
# original: pristine construction checkout, rebuilt from clean source
(cd $C/checkouts/$D4J && git reset -q -- . && git checkout -- . && rm -rf build target build-tests && defects4j compile > $E/$S/compile_original.log 2>&1 && echo "original recompiled")
restore $C/configs/$S/pair_config_low.json  $A/repro/$LOW-checkout  $A/repro/$LOW-correct
restore $C/configs/$S/pair_config_high.json $A/repro/$HIGH-checkout $A/repro/$HIGH-correct
run $C/checkouts/$D4J original
run $A/repro/$LOW-checkout low_buggy
run $A/repro/$HIGH-checkout high_buggy
run $A/repro/$LOW-correct low_correct
run $A/repro/$HIGH-correct high_correct
$PY - "$E/$S" "$S" "$LOW" "$HIGH" <<'PYX'
import sys,json,os
E,S,LOW,HIGH=sys.argv[1:5]
L={n:open(f"{E}/out_{n}.txt").read().splitlines() for n in ("original","low_buggy","high_buggy","low_correct","high_correct")}
n=len(L["original"]); eq=lambda a,b: sum(1 for x,y in zip(L[a],L[b]) if x==y)
res={"pair":S,"low":LOW,"high":HIGH,"cases":n,
 "lengths":{k:len(v) for k,v in L.items()},
 "low_correct_equals_original":eq("low_correct","original"),
 "high_correct_equals_original":eq("high_correct","original"),
 "low_buggy_equals_high_buggy":eq("low_buggy","high_buggy"),
 "cases_where_bug_changes_output":sum(1 for x,y in zip(L["original"],L["low_buggy"]) if x!=y)}
res["overall"]="pass" if (len(set(res["lengths"].values()))==1 and res["low_correct_equals_original"]==n
  and res["high_correct_equals_original"]==n and res["low_buggy_equals_high_buggy"]==n
  and res["cases_where_bug_changes_output"]>0) else "FAIL"
json.dump(res,open(f"{E}/equivalence.json","w"),indent=1); print(json.dumps(res))
PYX
