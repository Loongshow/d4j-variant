#!/bin/zsh
# Installs the ten scale-up packages ADDITIVELY into the frozen v3 server root (new_bug_variants/<Proj>/bug-1/L20/<ID>/), refusing to overwrite,
# then verifies byte-identity and dynamic discovery through /api/variants. NON-CANONICAL / CORE BENCHMARK SCALE-UP / GPT-5.6 EXECUTION.
set -euo pipefail
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v1; V3=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3; PY=/opt/miniconda3/bin/python
typeset -A PROJ; PROJ=(chart Chart math Math lang Lang)
for pb in chart/bug-02 chart/bug-03 math/bug-02 math/bug-03 lang/bug-02; do
  P=${PROJ[${pb%%/*}]}
  for pk in $S/$pb/packages/*; do
    V=$(basename $pk); DST=$V3/new_bug_variants/$P/bug-1/L20/$V
    if [ -e "$DST" ]; then echo "exists (not overwritten): $DST"; else mkdir -p "$(dirname $DST)"; cp -R "$pk" "$DST"; echo "installed: $V -> $DST"; fi
    (cd "$pk" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) | diff - <(cd "$DST" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) > /dev/null && echo "  byte-identical: $V" || { echo "  MISMATCH: $V"; exit 2; }
  done
done
curl -s "http://127.0.0.1:8792/api/variants" | $PY -c "
import json,sys; d=json.load(sys.stdin); recs=d if isinstance(d,list) else d.get('variants',d.get('records',[])); ids={r.get('variant_id') or r.get('id') for r in recs}
need={'CHART-POLAR-CONTROL-02','CHART-POLAR-TREATMENT-02','CHART-PIE-CONTROL-03','CHART-PIE-TREATMENT-03','MATH-BICUBIC-CONTROL-02','MATH-BICUBIC-TREATMENT-02','MATH-HARMONIC-CONTROL-03','MATH-HARMONIC-TREATMENT-03','LANG-FOLD-CONTROL-02','LANG-FOLD-TREATMENT-02'}
miss=need-ids; print('discovered by the server:', len(need-miss), 'of 10; missing:', sorted(miss) or 'none')
for r in recs:
    if (r.get('variant_id') or r.get('id')) in need: print('  ', r.get('variant_id'), '|', r.get('project'), '| gold', r.get('faulty_class','').split('.')[-1]+'#'+str(r.get('faulty_method')), '| trigger', str(r.get('triggering_test'))[-40:], '| val', r.get('validation_status'), '| repro', r.get('reproducibility_status'))
sys.exit(0 if not miss else 3)"
