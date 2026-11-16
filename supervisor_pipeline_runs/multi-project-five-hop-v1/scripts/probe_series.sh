#!/bin/zsh
# Three bounded smoke probes spaced 5 minutes apart (one tiny paid call each); records status and wall time. Used only to sample provider request health.
MP=/Users/shawnli/Desktop/Honours/defects4j/supervisor_pipeline_runs/multi-project-five-hop-v1; PY=/opt/miniconda3/bin/python
for n in 2 3 4; do
  START=$(date +%s); code=$(curl -s --max-time 400 -X POST http://127.0.0.1:8792/api/agents/mini-swe-agent/smoke-test -H 'content-type: application/json' -d '{"agent_id":"mini-swe-agent-openai-gpt-5-6"}' -o $MP/diagnostic/probe_smoke_$n.json -w '%{http_code}'); EL=$(( $(date +%s) - START ))
  ST=$($PY -c "import json;d=json.load(open('$MP/diagnostic/probe_smoke_$n.json'));print(d.get('status'))" 2>/dev/null)
  echo "probe $n at $(date -u +%FT%TZ): http $code | elapsed ${EL}s | status $ST"
  [ $n -lt 4 ] && sleep 300
done
echo "probe series finished $(date -u +%FT%TZ)"
