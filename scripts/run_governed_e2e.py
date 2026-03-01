#!/usr/bin/env python3
"""Run 3 consecutive governed end-to-end checks with evidence output."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "task-packet.alpha.json"
APPROVALS = ROOT / "audit" / "approvals"
REPORTS = ROOT / "reports"


def sh(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def nowz() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_once(idx: int) -> dict:
    task_id = f"ALPHA-20260301-3{idx:02d}"
    packet_path = Path(f"/tmp/{task_id}.json")

    data = json.loads(EXAMPLE.read_text())
    data["taskId"] = task_id
    data["riskLevel"] = "high"
    data["approvalsNeeded"]["securityReview"] = True
    data["approvalsNeeded"]["humanApproval"] = True
    data["audit"]["updatedAt"] = nowz()
    packet_path.write_text(json.dumps(data, indent=2))

    task_approval = {
        "taskId": task_id,
        "securityReviewApproved": True,
        "humanApproved": True,
        "approvedBy": "adarsh",
        "approvedAt": nowz(),
    }
    (APPROVALS / f"{task_id}.json").write_text(json.dumps(task_approval, indent=2))

    rc_assign, out_assign = sh(["python3", str(ROOT / "scripts" / "assign_task.py"), str(packet_path)])

    cmd = f"echo E2E_RUN_{idx}_OK"
    exec_approval_id = f"APPROVAL-20260301-E2E-{idx:02d}"
    exec_approval = {
        "approvalId": exec_approval_id,
        "riskLevel": "high",
        "humanApproved": True,
        "approvedBy": "adarsh",
        "expiresAt": "2099-01-01T00:00:00Z",
        "commandSha256": hashlib.sha256(cmd.encode()).hexdigest(),
    }
    (APPROVALS / f"{exec_approval_id}.json").write_text(json.dumps(exec_approval, indent=2))

    rc_exec, out_exec = sh([str(ROOT / "scripts" / "guarded_exec.sh"), "--approval-id", exec_approval_id, "--", cmd])

    rc_monitor, out_monitor = sh(["python3", str(ROOT / "scripts" / "monitor_factory.py")])

    ok = rc_assign == 0 and rc_exec == 0 and rc_monitor == 0 and f"E2E_RUN_{idx}_OK" in out_exec

    return {
        "run": idx,
        "taskId": task_id,
        "assign": {"rc": rc_assign, "ok": rc_assign == 0, "out": out_assign[-500:]},
        "guardedExec": {"rc": rc_exec, "ok": rc_exec == 0, "out": out_exec[-500:]},
        "monitor": {"rc": rc_monitor, "ok": rc_monitor == 0, "out": out_monitor[-500:]},
        "ok": ok,
    }


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    APPROVALS.mkdir(parents=True, exist_ok=True)

    started = nowz()
    results = [run_once(i) for i in range(1, 4)]
    payload = {
        "startedAt": started,
        "finishedAt": nowz(),
        "allOk": all(r["ok"] for r in results),
        "results": results,
    }

    out = REPORTS / "governed-e2e.latest.json"
    out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))

    return 0 if payload["allOk"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
