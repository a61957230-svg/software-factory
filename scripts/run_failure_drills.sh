#!/usr/bin/env bash
set -euo pipefail

# Failure drill runner (safe-by-default: dry run)
# Drills:
# 1) token compromise rotation check
# 2) config rollback check
# 3) gateway recovery restart check

MODE="dry-run"
if [[ "${1:-}" == "--execute" ]]; then
  MODE="execute"
fi

ROOT="/home/adarsh/.openclaw"
CFG="$ROOT/openclaw.json"
ENVF="$ROOT/.env"
REPORT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/reports"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/failure-drills.latest.txt"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$REPORT"; }

: > "$REPORT"
log "MODE=$MODE"

log "Drill1 token-compromise: verify env-substitution present"
python3 - <<'PY' | tee -a "$REPORT"
import json
from pathlib import Path
cfg=Path('/home/adarsh/.openclaw/openclaw.json')
d=json.loads(cfg.read_text())
checks={
 'hooks.token': d['hooks']['token'],
 'gateway.auth.token': d['gateway']['auth']['token'],
 'channels.telegram.botToken': d['channels']['telegram']['botToken'],
}
for k,v in checks.items():
    print(k, 'OK' if isinstance(v,str) and v.startswith('${') else f'BAD:{v}')
PY

log "Drill2 rollback: latest config backup exists"
ls -1t "$ROOT"/openclaw.json.backup* 2>/dev/null | head -n 3 | tee -a "$REPORT" || true

log "Drill3 gateway recovery"
if [[ "$MODE" == "execute" ]]; then
  openclaw gateway restart | tee -a "$REPORT"
  openclaw status --deep | tee -a "$REPORT"
else
  log "DRY: would run 'openclaw gateway restart' and 'openclaw status --deep'"
fi

log "DONE"
