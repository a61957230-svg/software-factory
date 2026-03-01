#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$BASE_DIR/reports/evidence-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT_DIR"

# Core captures
openclaw status --deep > "$OUT_DIR/openclaw-status-deep.txt" 2>&1 || true
openclaw security audit --deep > "$OUT_DIR/openclaw-security-audit-deep.txt" 2>&1 || true
openclaw doctor --non-interactive > "$OUT_DIR/openclaw-doctor.txt" 2>&1 || true

# Factory artifacts
cp -f "$BASE_DIR/schemas/task-packet.schema.json" "$OUT_DIR/" || true
cp -f "$BASE_DIR/scripts/validate_task_packet.py" "$OUT_DIR/" || true
cp -f "$BASE_DIR/scripts/assign_task.py" "$OUT_DIR/" || true
cp -f "$BASE_DIR/scripts/monitor_factory.py" "$OUT_DIR/" || true
cp -f "$BASE_DIR/scripts/guarded_exec.sh" "$OUT_DIR/" || true
cp -f "$BASE_DIR/reports/monitor.latest.json" "$OUT_DIR/" 2>/dev/null || true
cp -f "$BASE_DIR/reports/parallel-sim.latest.json" "$OUT_DIR/" 2>/dev/null || true
cp -f "$BASE_DIR/reports/failure-drills.latest.txt" "$OUT_DIR/" 2>/dev/null || true

# Queue + audit snapshots
mkdir -p "$OUT_DIR/queue" "$OUT_DIR/audit"
find "$BASE_DIR/queue" -type f -maxdepth 3 -print > "$OUT_DIR/queue/files.txt" || true
find "$BASE_DIR/audit" -type f -maxdepth 3 -print > "$OUT_DIR/audit/files.txt" || true

cat > "$OUT_DIR/SIGNOFF_TEMPLATE.md" <<'EOF'
# Final Signoff

- Date:
- Operator:
- Scope:

## Controls Checklist
- [ ] 0 critical findings
- [ ] Merge/deploy gates enforced
- [ ] 3 consecutive end-to-end runs passed
- [ ] Audit trail complete and queryable
- [ ] Rollback + incident drills passed

## Decision
- [ ] Approved for production
- [ ] Approved for pilot only
- [ ] Not approved

## Notes

EOF

echo "Evidence pack created: $OUT_DIR"
