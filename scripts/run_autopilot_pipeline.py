#!/usr/bin/env python3
"""Automated Research -> Plan -> Develop -> Review -> Release pipeline runner.

This script orchestrates a full governed flow for one task packet and writes
stage artifacts into the task workspace.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
QUEUE = ROOT / "queue"

LEAD_BY_PROJECT = {
    "alpha": "lead-project-alpha",
    "beta": "lead-project-beta",
    "gamma": "lead-project-gamma",
}

WORKER_BY_TYPE = {
    "feature": "backend-worker",
    "bugfix": "backend-worker",
    "refactor": "backend-worker",
    "security": "security-reviewer",
    "infra": "devops-worker",
    "docs": "docs-release-writer",
    "release": "release-gatekeeper",
}

SANDBOXED_AGENTS = {
    "backend-worker",
    "frontend-worker",
    "qa-worker",
    "devops-worker",
    "docs-release-writer",
    "code-reviewer",
    "security-reviewer",
    "release-gatekeeper",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(cmd: List[str], *, cwd: Path | None = None, timeout: int | None = None) -> Tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return p.returncode, p.stdout, p.stderr


def run_json_agent(agent_id: str, message: str, *, timeout_sec: int = 240) -> Dict[str, Any]:
    """Run an agent in local mode and return normalized output."""
    base = [
        "openclaw",
        "agent",
        "--local",
        "--agent",
        agent_id,
        "--message",
        message,
        "--json",
    ]

    try:
        if agent_id in SANDBOXED_AGENTS:
            cmd_str = " ".join(shlex.quote(x) for x in base)
            rc, out, err = run(["sg", "docker", "-c", cmd_str], cwd=ROOT, timeout=timeout_sec)
        else:
            rc, out, err = run(base, cwd=ROOT, timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"agent timeout ({agent_id}) after {timeout_sec}s")

    if rc != 0:
        raise RuntimeError(f"agent run failed ({agent_id}): {err.strip() or out.strip()}")

    payload = json.loads(out)
    # normalize gateway/local shapes
    if "result" in payload:
        result = payload.get("result", {})
        text = (result.get("payloads") or [{}])[0].get("text", "")
        meta = result.get("meta", {})
    else:
        text = (payload.get("payloads") or [{}])[0].get("text", "")
        meta = payload.get("meta", {})

    return {
        "agentId": agent_id,
        "text": text,
        "meta": meta,
        "stderr": err.strip(),
    }


def emit_event(event: Dict[str, Any]) -> None:
    cmd = [
        "python3",
        str(SCRIPTS / "emit_audit_event.py"),
        "--event",
        json.dumps(event),
    ]
    rc, out, err = run(cmd, cwd=ROOT)
    if rc != 0:
        raise RuntimeError(f"emit event failed: {err or out}")


def stage_prompt(stage: str, packet: Dict[str, Any], task_dir: Path) -> str:
    title = packet.get("title", "")
    desc = packet.get("description", "")
    ac = "\n".join(f"- {x}" for x in packet.get("acceptanceCriteria", []))

    if stage == "research":
        return (
            f"Task: {title}\nDescription: {desc}\n"
            f"Acceptance Criteria:\n{ac}\n\n"
            "Provide concise technical research notes: best approach, risks, dependencies, and 3 implementation tips."
        )
    if stage == "plan":
        return (
            f"Create implementation plan for task {packet['taskId']} ({title}).\n"
            f"Scope: {desc}\nAC:\n{ac}\n"
            "Return steps with owner + estimates + test strategy."
        )
    if stage == "develop":
        return (
            f"Simulate development execution plan for {packet['taskId']} ({title}).\n"
            "Return concrete file-level changes, test cases, and commit plan."
        )
    if stage == "review":
        return (
            f"Review package for {packet['taskId']}.\n"
            "Given planned changes, provide code-review checklist, security findings, and go/no-go with reasons."
        )
    if stage == "release":
        return (
            f"Prepare release gate decision for {packet['taskId']}.\n"
            "Return release checklist, rollback steps, and final decision format: APPROVE or BLOCK with reason."
        )
    raise ValueError(stage)


def write_stage_artifact(task_dir: Path, stage: str, prompt: str, result: Dict[str, Any]) -> Path:
    artifacts = task_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    p = artifacts / f"{stage}.md"
    content = [
        f"# Stage: {stage}",
        "",
        f"- agent: `{result['agentId']}`",
        f"- timestamp: `{now_iso()}`",
        "",
        "## Prompt",
        "```",
        prompt,
        "```",
        "",
        "## Output",
        result.get("text", "").strip() or "(no output)",
    ]
    if result.get("stderr"):
        content += ["", "## Stderr", "```", result["stderr"], "```"]
    p.write_text("\n".join(content) + "\n")
    return p


def update_done_packet(packet: Dict[str, Any], done_path: Path) -> None:
    packet = json.loads(json.dumps(packet))
    packet["lifecycleStage"] = "done"
    packet["nextAgent"] = "release-gatekeeper"
    packet["audit"]["updatedAt"] = now_iso()
    done_path.parent.mkdir(parents=True, exist_ok=True)
    done_path.write_text(json.dumps(packet, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run automated governed SDLC pipeline for one task packet")
    ap.add_argument("packet", help="Path to task packet json")
    args = ap.parse_args()

    packet_path = Path(args.packet).resolve()
    if not packet_path.exists():
        raise SystemExit(f"ERROR: packet not found: {packet_path}")

    packet = json.loads(packet_path.read_text())
    task_id = packet["taskId"]
    project = packet["projectKey"]
    lead = LEAD_BY_PROJECT.get(project, "lead-project-alpha")
    worker = WORKER_BY_TYPE.get(packet.get("type", "feature"), "backend-worker")

    # 1) validate
    rc, out, err = run(["python3", str(SCRIPTS / "validate_task_packet.py"), str(packet_path)], cwd=ROOT)
    if rc != 0:
        raise SystemExit(f"VALIDATION_FAILED: {err or out}")

    # 2) assign
    rc, out, err = run(["python3", str(SCRIPTS / "assign_task.py"), str(packet_path)], cwd=ROOT)
    if rc != 0:
        raise SystemExit(f"ASSIGNMENT_FAILED: {err or out}")

    # 3) task workspace
    title = packet.get("title", "Task")
    rc, out, err = run([str(SCRIPTS / "new_task.sh"), project, task_id, title, lead], cwd=ROOT)
    if rc != 0:
        raise SystemExit(f"TASK_WORKSPACE_FAILED: {err or out}")

    task_dir = ROOT / "projects" / project / "tasks" / task_id

    stages = [
        ("research", "researcher"),
        ("plan", lead),
        ("develop", worker),
        ("review", "code-reviewer"),
        ("release", "release-gatekeeper"),
    ]

    summary = {
        "taskId": task_id,
        "projectKey": project,
        "startedAt": now_iso(),
        "stages": [],
    }

    for stage, agent in stages:
        started = time.time()
        prompt = stage_prompt(stage, packet, task_dir)
        print(f"[autopilot] stage={stage} agent={agent} start", flush=True)

        emit_event(
            {
                "eventId": f"evt-{task_id}-{stage}-start-{int(started)}",
                "timestamp": now_iso(),
                "projectKey": project,
                "taskId": task_id,
                "agentId": agent,
                "action": f"pipeline.{stage}.start",
                "status": "success",
                "resource": str(packet_path),
            }
        )

        try:
            result = run_json_agent(agent, prompt)
            artifact = write_stage_artifact(task_dir, stage, prompt, result)
            duration = int((time.time() - started) * 1000)

            emit_event(
                {
                    "eventId": f"evt-{task_id}-{stage}-done-{int(time.time())}",
                    "timestamp": now_iso(),
                    "projectKey": project,
                    "taskId": task_id,
                    "agentId": agent,
                    "action": f"pipeline.{stage}.done",
                    "status": "success",
                    "resource": str(artifact),
                    "durationMs": duration,
                }
            )

            summary["stages"].append(
                {
                    "stage": stage,
                    "agent": agent,
                    "status": "success",
                    "artifact": str(artifact),
                    "durationMs": duration,
                }
            )
            print(f"[autopilot] stage={stage} done ({duration}ms)", flush=True)
        except Exception as e:
            duration = int((time.time() - started) * 1000)
            emit_event(
                {
                    "eventId": f"evt-{task_id}-{stage}-fail-{int(time.time())}",
                    "timestamp": now_iso(),
                    "projectKey": project,
                    "taskId": task_id,
                    "agentId": agent,
                    "action": f"pipeline.{stage}.done",
                    "status": "failure",
                    "durationMs": duration,
                    "resource": str(packet_path),
                }
            )
            summary["stages"].append(
                {
                    "stage": stage,
                    "agent": agent,
                    "status": "failure",
                    "error": str(e),
                    "durationMs": duration,
                }
            )
            print(f"[autopilot] stage={stage} FAILED: {e}", flush=True)
            summary["finishedAt"] = now_iso()
            summary["allOk"] = False
            out = ROOT / "reports" / "autopilot.latest.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(summary, indent=2))
            print(json.dumps(summary, indent=2))
            return 2

    done_packet = QUEUE / "done" / project / f"{task_id}.json"
    update_done_packet(packet, done_packet)

    emit_event(
        {
            "eventId": f"evt-{task_id}-pipeline-complete-{int(time.time())}",
            "timestamp": now_iso(),
            "projectKey": project,
            "taskId": task_id,
            "agentId": "router",
            "action": "pipeline.completed",
            "status": "success",
            "resource": str(done_packet),
        }
    )

    summary["finishedAt"] = now_iso()
    summary["allOk"] = True
    summary["donePacket"] = str(done_packet)

    out = ROOT / "reports" / "autopilot.latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
