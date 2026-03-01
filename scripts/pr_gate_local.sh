#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[gate] validate sample packet"
python3 scripts/validate_task_packet.py examples/task-packet.alpha.json

echo "[gate] monitor"
python3 scripts/monitor_factory.py >/tmp/factory-monitor.json

if grep -q '"alerts": \[\]' /tmp/factory-monitor.json; then
  echo "[gate] monitor clean"
else
  echo "[gate] monitor alerts present"
  cat /tmp/factory-monitor.json
  exit 2
fi

echo "[gate] parallel sim"
python3 scripts/simulate_parallel_load.py >/tmp/factory-parallel.json

echo "[gate] PASS"
