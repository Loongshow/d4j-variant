#!/bin/zsh
# Installs the twelve v2 packages ADDITIVELY into the frozen v3 server root (new_bug_variants/<Proj>/bug-1/L20/<ID>/), refusing to overwrite,
# then verifies byte-identity and dynamic discovery through /api/variants. NON-CANONICAL / CORE BENCHMARK SCALE-UP V2 / GPT-5.6.
set -euo pipefail
S=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/core-benchmark-scaleup-v2; V3=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/diagnostic-noncanonical-v3; PY=/opt/miniconda3/bin/python
for pb in projects/Compress/bug-01 projects/Compress/bug-02 projects/Compress/bug-03 projects/JacksonCore/bug-04 projects/JacksonCore/bug-05 projects/Compress/bug-06; do
  P=$($PY -c "import json;print(json.load(open('$S/$pb/pair_config.json'))['project'])")
  for pk in $S/$pb/packages/*; do
    V=$(basename $pk); DST=$V3/new_bug_variants/$P/bug-1/L20/$V
    if [ -e "$DST" ]; then echo "exists (not overwritten): $V"; else mkdir -p "$(dirname $DST)"; cp -R "$pk" "$DST"; echo "installed: $V"; fi
    (cd "$pk" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) | diff - <(cd "$DST" && shasum -a 256 variant.patch test.patch variant_manifest.json validation.json NON_CANONICAL.md) > /dev/null && echo "  byte-identical: $V" || { echo "  MISMATCH: $V"; exit 2; }
  done
done
curl -s "http://127.0.0.1:8792/api/variants" | $PY -c "
import json,sys; d=json.load(sys.stdin); recs=d if isinstance(d,list) else d.get('variants',d.get('records',[])); ids={r.get('variant_id') or r.get('id') for r in recs}
need={'CMP-CKSUM-CONTROL-01','CMP-CKSUM-TREATMENT-01','CMP-LAYOUT-CONTROL-02','CMP-LAYOUT-TREATMENT-02','CMP-OCTAL-CONTROL-03','CMP-OCTAL-TREATMENT-03','JKC-SURR-CONTROL-04','JKC-SURR-TREATMENT-04','JKC-OFFSET-CONTROL-05','JKC-OFFSET-TREATMENT-05','CMP-ALIGN-CONTROL-06','CMP-ALIGN-TREATMENT-06'}
miss=need-ids; print('discovered by the server:', len(need-miss), 'of 12; missing:', sorted(miss) or 'none')
for r in recs:
    if (r.get('variant_id') or r.get('id')) in need: print('  ', r.get('variant_id'), '|', r.get('project'), '|', str(r.get('faulty_class','')).split('.')[-1]+'#'+str(r.get('faulty_method')), '| val', r.get('validation_status'), '| repro', r.get('reproducibility_status'))
sys.exit(0 if not miss else 3)"
