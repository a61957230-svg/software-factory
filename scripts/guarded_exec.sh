#!/usr/bin/env bash
set -euo pipefail

# Requires explicit human approval artifact for dangerous commands.
# Usage:
#   ./scripts/guarded_exec.sh --approval-id APPROVAL-20260301-001 -- "rm -rf /tmp/test"

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPROVALS_DIR="$BASE_DIR/audit/approvals"
LOG_DIR="$BASE_DIR/audit/events"

if [[ $# -lt 3 || "$1" != "--approval-id" ]]; then
  echo "Usage: $0 --approval-id <ID> -- <command>"
  exit 1
fi

APPROVAL_ID="$2"
shift 2
[[ "$1" == "--" ]] || { echo "Expected -- before command"; exit 1; }
shift

CMD="$*"
APPROVAL_FILE="$APPROVALS_DIR/$APPROVAL_ID.json"

if [[ ! -f "$APPROVAL_FILE" ]]; then
  echo "DENY: missing approval file $APPROVAL_FILE"
  exit 2
fi

if ! python3 - "$APPROVAL_FILE" "$CMD" <<'PY'
import json, hashlib, sys
p, cmd = sys.argv[1], sys.argv[2]
d = json.load(open(p))
if not d.get('humanApproved', False):
    raise SystemExit('DENY: humanApproved=false')
if not d.get('approvedBy'):
    raise SystemExit('DENY: approvedBy missing')
exp = d.get('expiresAt')
if not exp:
    raise SystemExit('DENY: expiresAt missing')
if d.get('commandSha256'):
    h = hashlib.sha256(cmd.encode()).hexdigest()
    if h != d['commandSha256']:
        raise SystemExit('DENY: command hash mismatch')
print('OK')
PY
then
  exit 3
fi

# Command classification (coarse): require explicit risk tag
if ! python3 - "$APPROVAL_FILE" <<'PY'
import json,sys
p=sys.argv[1]
d=json.load(open(p))
risk=d.get('riskLevel','').lower()
if risk not in {'high','critical'}:
    raise SystemExit('DENY: riskLevel must be high|critical for guarded exec')
print('RISK_OK')
PY
then
  exit 4
fi

mkdir -p "$LOG_DIR"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
EVENT_FILE="$LOG_DIR/$(date -u +%Y-%m-%d).jsonl"

echo "Executing approved command..."
set +e
bash -lc "$CMD"
EC=$?
set -e

STATUS="success"
[[ $EC -eq 0 ]] || STATUS="failure"

python3 - <<PY
import json
from datetime import datetime, timezone
event={
  "eventId": f"evt-guarded-exec-{int(datetime.now().timestamp())}",
  "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
  "projectKey": "global",
  "taskId": "$APPROVAL_ID",
  "agentId": "release-gatekeeper",
  "action": "guarded.exec",
  "resource": "$CMD"[:200],
  "status": "$STATUS",
  "approvalRef": "$APPROVAL_ID"
}
with open("$EVENT_FILE","a",encoding="utf-8") as f:
    f.write(json.dumps(event)+"\\n")
print("Logged", event["eventId"])
PY

exit $EC
