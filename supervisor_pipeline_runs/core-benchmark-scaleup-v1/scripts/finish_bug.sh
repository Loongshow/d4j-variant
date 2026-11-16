#!/bin/zsh
# After validation: fresh reproduction + lexgate, equivalence probe, structural audit, token surface, packaging and evidence docs for one bug.
# Usage: finish_bug.sh <proj> <bug> <D4J project> <ProbeClass> <token> [<token> ...]
export PERL5LIB=$HOME/perl5/lib/perl5; S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1; PY=/opt/miniconda3/bin/python
P=$1; B=$2; D4J=$3; CLS=$4; shift 4
cd $S && zsh scripts/repro_and_lexgate.sh $P $B $D4J 2>&1 | grep -E 'overall|lexgate' | cut -c1-200
zsh scripts/equivalence_probe.sh $P $B $D4J $CLS 2>&1 | tail -1
$PY scripts/structural_audit.py $P/$B/pair_config.json $P/$B/repro/treatment-checkout $P/$B/analysis/structural_audit.json | tail -1
$PY scripts/token_surface.py $P/$B/pair_config.json $P/$B/repro/control-checkout $P/$B/repro/treatment-checkout $P/$B/analysis/leakage/token_surface.json $P/$B/analysis/leakage/token_surface.md "$@" > /dev/null 2>&1 && echo "token surface written"
$PY scripts/package_bug.py $P/$B/pair_config.json $P $B
$PY scripts/write_bug_docs.py $P $B
