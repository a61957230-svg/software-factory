#!/usr/bin/env python3
"""Basic factory observability checks for queue backlogs and stale tasks."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
QUEUE_DIR = BASE_DIR / "queue"
APPROVALS_DIR = BASE_DIR / "audit" / "approvals"
REPORTS_DIR = BASE_DIR / "reports"


@dataclass
class Alert:
    level: str
    code: str
    message: str


def _count_files(path: Path, pattern: str = "*.json") -> int:
    if not path.exists():
        return 0
    return len(list(path.rglob(pattern)))


def _stale_assigned(hours: int) -> list[Path]:
    stale = []
    now = datetime.now(timezone.utc).timestamp()
    for p in (QUEUE_DIR / "assigned").rglob("*.json"):
        age_h = (now - p.stat().st_mtime) / 3600
        if age_h >= hours:
            stale.append(p)
    return stale


def _pending_approvals() -> list[Path]:
    pending = []
    for p in APPROVALS_DIR.rglob("*.json"):
        try:
            d = json.loads(p.read_text())
            if not d.get("humanApproved") or not d.get("securityReviewApproved", True):
                pending.append(p)
        except Exception:
            pending.append(p)
    return pending


def main() -> int:
    parser = argparse.ArgumentParser(description="Factory queue/approval health monitor")
    parser.add_argument("--stale-hours", type=int, default=6)
    parser.add_argument("--max-intake", type=int, default=20)
    parser.add_argument("--max-blocked", type=int, default=10)
    args = parser.parse_args()

    intake = _count_files(QUEUE_DIR / "intake")
    assigned = _count_files(QUEUE_DIR / "assigned")
    blocked = _count_files(QUEUE_DIR / "blocked")
    done = _count_files(QUEUE_DIR / "done")

    alerts: list[Alert] = []
    if intake > args.max_intake:
        alerts.append(Alert("warn", "INTAKE_BACKLOG", f"intake backlog high: {intake}"))
    if blocked > args.max_blocked:
        alerts.append(Alert("warn", "BLOCKED_BACKLOG", f"blocked backlog high: {blocked}"))

    stale = _stale_assigned(args.stale_hours)
    if stale:
        alerts.append(Alert("warn", "STALE_ASSIGNED", f"{len(stale)} assigned tasks stale >= {args.stale_hours}h"))

    pending = _pending_approvals()
    if pending:
        alerts.append(Alert("warn", "APPROVAL_BACKLOG", f"{len(pending)} approval files pending"))

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "counts": {
            "intake": intake,
            "assigned": assigned,
            "blocked": blocked,
            "done": done,
            "pendingApprovals": len(pending),
            "staleAssigned": len(stale),
        },
        "alerts": [a.__dict__ for a in alerts],
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "monitor.latest.json"
    out.write_text(json.dumps(payload, indent=2))

    print(json.dumps(payload, indent=2))
    if alerts:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
