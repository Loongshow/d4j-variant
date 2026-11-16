#!/bin/zsh
# Executes a probe class against four build states: original (screening checkout), CONTROL (buggy, repro checkout), TREATMENT (buggy chain, repro
# checkout) and a temporary CORRECT-CHAIN build (treatment repro checkout copy with the gold line restored). Asserts original == correct chain and
# control == treatment on every case. Usage: equivalence_probe.sh <proj> <bug> <D4J project> <ProbeClass>
export PERL5LIB=$HOME/perl5/lib/perl5; S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2; PY=/opt/miniconda3/bin/python
P=$1; B=$2; D4J=$3; CLS=$4; ORIG=${5:-$S/screening/$D4J}; CFG=$S/$P/$B/pair_config.json; E=$S/$P/$B/analysis/equivalence; SRC=$E/$CLS.java
CC=$S/$P/$B/repro/treatment-correct-checkout; rm -rf $CC; cp -R $S/$P/$B/repro/treatment-checkout $CC
$PY - "$CFG" "$CC" <<'PY'
import json, sys; cfg=json.load(open(sys.argv[1])); A=cfg["treatment"]; p=sys.argv[2]+"/"+A["gold_file"]
raw=open(p,"rb").read().decode(); eol="\r\n" if "\r\n" in raw else "\n"; t=raw.replace("\r\n","\n"); assert t.count(A["bug_line"])==1
open(p,"wb").write(t.replace(A["bug_line"],A["orig_line"],1).replace("\n",eol).encode()); print("gold line restored in the correct-chain copy")
PY
GF=$($PY -c "import json;print(json.load(open('$CFG'))['treatment']['gold_file'])"); GN=$(basename $GF .java); GD=$(dirname $GF | sed -e 's#^source/##' -e 's#^src/main/java/##')
for d in build target/classes; do [ -d $CC/$d/$GD ] && find $CC/$d/$GD -maxdepth 1 -name "$GN.class" -o -maxdepth 1 -name "$GN\$*.class" | xargs rm -f; done
(cd $CC && defects4j compile > $E/compile_correct_chain.log 2>&1 && echo "correct-chain copy compiled (gold class rebuilt)")
run() { CO=$1; NAME=$2; CP=$(cd $CO && defects4j export -p cp.test 2>/dev/null | tail -1); mkdir -p $E/build_$NAME; javac -cp "$CP" -d $E/build_$NAME $SRC && java -cp "$CP:$E/build_$NAME" $CLS > $E/out_$NAME.txt; echo "$NAME: $(wc -l < $E/out_$NAME.txt) cases"; }
run $ORIG original; run $S/$P/$B/repro/control-checkout control_buggy; run $S/$P/$B/repro/treatment-checkout treatment_buggy; run $CC treatment_correct
$PY - "$E" <<'PY'
import sys, json; E=sys.argv[1]; L={n: open(f"{E}/out_{n}.txt").read().splitlines() for n in ("original","control_buggy","treatment_buggy","treatment_correct")}
n=len(L["original"]); eq1=sum(1 for a,b in zip(L["original"],L["treatment_correct"]) if a==b); eq2=sum(1 for a,b in zip(L["control_buggy"],L["treatment_buggy"]) if a==b)
diff=sum(1 for a,b in zip(L["original"],L["control_buggy"]) if a!=b)
res={"cases":n,"original_equals_correct_chain":eq1,"control_buggy_equals_treatment_buggy":eq2,"cases_where_bug_changes_output":diff,"overall":"pass" if eq1==n and eq2==n and diff>0 else "FAIL"}
json.dump(res,open(f"{E}/equivalence.json","w"),indent=1); print(json.dumps(res))
PY
