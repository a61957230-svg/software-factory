#!/usr/bin/env python3
"""Validate and route task packets from intake to assigned/blocked with audit events."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]
QUEUE_DIR = BASE_DIR / "queue"
AUDIT_APPROVALS = BASE_DIR / "audit" / "approvals"

REQUIRED = [
    "schemaVersion",
    "taskId",
    "projectKey",
    "title",
    "type",
    "priority",
    "riskLevel",
    "lifecycleStage",
    "acceptanceCriteria",
    "constraints",
    "approvalsNeeded",
    "relevantFiles",
    "ownerAgent",
    "nextAgent",
    "audit",
    "rollback",
]

TASK_RE = re.compile(r"^[A-Z]+-[0-9]{8}-[0-9]{3}$")
PROJ_RE = re.compile(r"^[a-z0-9-]{2,32}$")
ALLOWED_TYPE = {"feature", "bugfix", "refactor", "security", "infra", "docs", "release"}
ALLOWED_PRIORITY = {"P0", "P1", "P2", "P3"}
ALLOWED_RISK = {"low", "medium", "high", "critical"}
ALLOWED_STAGE = {"intake", "breakdown", "assignment", "implementation", "review", "release", "done", "blocked"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _emit(event: Dict[str, Any]) -> None:
    from emit_audit_event import append_event, validate_event  # local script

    validate_event(event)
    append_event(event)


def validate_packet(data: Dict[str, Any]) -> Tuple[bool, str]:
    for k in REQUIRED:
        if k not in data:
            return False, f"Missing required field: {k}"

    if data["schemaVersion"] != "1.0.0":
        return False, "schemaVersion must be 1.0.0"
    if not TASK_RE.match(data["taskId"]):
        return False, "taskId format invalid"
    if not PROJ_RE.match(data["projectKey"]):
        return False, "projectKey format invalid"
    if data["type"] not in ALLOWED_TYPE:
        return False, "type invalid"
    if data["priority"] not in ALLOWED_PRIORITY:
        return False, "priority invalid"
    if data["riskLevel"] not in ALLOWED_RISK:
        return False, "riskLevel invalid"
    if data["lifecycleStage"] not in ALLOWED_STAGE:
        return False, "lifecycleStage invalid"

    if not isinstance(data["acceptanceCriteria"], list) or not data["acceptanceCriteria"]:
        return False, "acceptanceCriteria must be non-empty array"

    approvals = data["approvalsNeeded"]
    for k in ["merge", "deploy", "securityReview", "humanApproval"]:
        if k not in approvals or not isinstance(approvals[k], bool):
            return False, f"approvalsNeeded.{k} missing or not boolean"

    if data["riskLevel"] in {"high", "critical"} and not approvals["securityReview"]:
        return False, "securityReview must be true for high/critical risk"
    if data["riskLevel"] in {"medium", "high", "critical"} and not approvals["humanApproval"]:
        return False, "humanApproval must be true for medium/high/critical risk"

    return True, "OK"


def check_required_approval(task_id: str, risk_level: str) -> Tuple[bool, str]:
    """Hard gate for high/critical tasks."""
    if risk_level not in {"high", "critical"}:
        return True, "OK"

    approval_file = AUDIT_APPROVALS / f"{task_id}.json"
    if not approval_file.exists():
        return False, f"Missing approval file: {approval_file}"

    payload = json.loads(approval_file.read_text())
    if not payload.get("securityReviewApproved"):
        return False, "securityReviewApproved must be true"
    if not payload.get("humanApproved"):
        return False, "humanApproved must be true"
    return True, "OK"


def block_packet(packet_path: Path, task_id: str, project_key: str, reason: str) -> Path:
    out = QUEUE_DIR / "blocked" / f"{task_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(packet_path, out)
    (out.with_suffix(".reason.txt")).write_text(reason + "\n")

    _emit(
        {
            "eventId": f"evt-{task_id}-blocked-{int(datetime.now().timestamp())}",
            "timestamp": now_iso(),
            "projectKey": project_key,
            "taskId": task_id,
            "agentId": "router",
            "action": "assignment.blocked",
            "resource": str(packet_path),
            "status": "blocked",
        }
    )
    return out


def assign_packet(packet_path: Path, data: Dict[str, Any]) -> Path:
    out = QUEUE_DIR / "assigned" / data["projectKey"] / f"{data['taskId']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(packet_path, out)

    _emit(
        {
            "eventId": f"evt-{data['taskId']}-assigned-{int(datetime.now().timestamp())}",
            "timestamp": now_iso(),
            "projectKey": data["projectKey"],
            "taskId": data["taskId"],
            "agentId": "router",
            "action": "assignment.assigned",
            "resource": str(packet_path),
            "status": "success",
        }
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a task packet with hard validation gates")
    parser.add_argument("packet", help="Path to task packet JSON")
    parser.add_argument("--move", action="store_true", help="Move packet out of intake on success/block")
    args = parser.parse_args()

    packet_path = Path(args.packet).resolve()
    if not packet_path.exists():
        raise SystemExit(f"ERROR: packet not found: {packet_path}")

    data = json.loads(packet_path.read_text())
    task_id = data.get("taskId", "UNKNOWN")
    project_key = data.get("projectKey", "unknown")

    ok, msg = validate_packet(data)
    if not ok:
        out = block_packet(packet_path, task_id, project_key, f"VALIDATION_FAILED: {msg}")
        print(f"BLOCKED: {msg} -> {out}")
        if args.move and packet_path.parent.name == "intake":
            packet_path.unlink(missing_ok=True)
        return 2

    ok, msg = check_required_approval(task_id, data["riskLevel"])
    if not ok:
        out = block_packet(packet_path, task_id, project_key, f"APPROVAL_GATE_FAILED: {msg}")
        print(f"BLOCKED: {msg} -> {out}")
        if args.move and packet_path.parent.name == "intake":
            packet_path.unlink(missing_ok=True)
        return 3

    out = assign_packet(packet_path, data)
    print(f"ASSIGNED: {task_id} -> {out}")
    if args.move and packet_path.parent.name == "intake":
        packet_path.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
