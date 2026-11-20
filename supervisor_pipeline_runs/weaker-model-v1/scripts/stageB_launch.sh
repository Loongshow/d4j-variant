#!/bin/zsh
# Stage B launch sequence (after all three audits are CONFIRMED and all twelve cells are packaged). Usage: stageB_launch.sh
# Steps: plan -> freeze (add-plan) -> /private/tmp audit -> server w55 -> driver preflight (--verify-only) -> run chain.
set -e
cd "$(dirname "$0")/.."
PY=/opt/miniconda3/bin/python; PLAN=${PLAN:-plans/B_stageB_gpt55_block1.json}
IIDS=${IIDS:-SB-B1-C00,SB-B1-C01,SB-B1-C10,SB-B1-C11,SB-B3-C00,SB-B3-C01,SB-B3-C10,SB-B3-C11}   # block 1 = the two audited bugs (W14); B2' later
SHA=$(shasum -a 256 STAGE_B_PREREGISTRATION.md | cut -c1-64)
[ -f $PLAN ] || $PY scripts/mx_plan.py $PLAN --iids $IIDS --runs 5 --seed 1014 --purpose "${PURPOSE:-Stage B 2x2 on gpt-5.5, block 1 (B1 Lang, B3 Chart; B2 withdrawn W14)}; STAGE_B_PREREGISTRATION.md sha256 $SHA"
$PY -c "import json;p=json.load(open('$PLAN'));print('plan slots:',len(p['slots']))"
grep -q "$PLAN" FREEZE.json || $PY scripts/mx_freeze.py --add-plan $PLAN --server w55
$PY scripts/mx_tmp_audit.py
zsh scripts/start_gpt_server.sh w55
sleep 8
$PY scripts/ct_driver.py --server w55 --plan $PLAN --verify-only
echo "preflight ok; launching the block"
zsh scripts/wm_run_chain.sh w55 ${TAG:-stageB_block1} $PLAN
